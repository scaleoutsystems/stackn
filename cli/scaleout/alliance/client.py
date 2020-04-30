import logging
import time
import threading
from scaleout.utils.dispatcher import Dispatcher
from scaleout.runtime.runtime import Runtime
from scaleout.repository.helpers import get_repository

import grpc
import pickle
import json

import proto.alliance_pb2 as alliance
import proto.alliance_pb2_grpc as rpc

logger = logging.getLogger(__name__)


class AllianceRuntimeClient(Runtime):
    """ A base RuntimeClient """ 

    def __init__(self):
        super(AllianceRuntimeClient, self).__init__(None, None)

        # Obtain a connection to the gRPC server (controller)
        alliance_config = self.config['Alliance']
        address = alliance_config['controller_host']
        port = alliance_config['controller_port'] 
        channel = grpc.insecure_channel(address + ":" + str(port))
        self.connection = rpc.AllianceServerStub(channel)
        print("Client: {} connected to {}:{}".format(self.client, address, port))

        # A client for the storage system used to hold models (e.g. Minio)
        # The project name and alliance id is used to compose the bucket name 
        self.repository = get_repository(config=alliance_config['Repository'])
        self.bucket_name = alliance_config["Repository"]["minio_bucket"]

    def get_model(self, model_id):
        print("trying to get model with id: {}".format(model_id))
        return self.repository.get_artifact(model_id)

    def get_global_model(self):

        request = alliance.Request()
        request.command = alliance.Request.GLOBALMODEL
        request.client = self.client
        self.connection.SendRequest(request)
        print("sent request for globalmodel!")

        # TODO WARNING BLOCKING CALL, set a timeout!
        for request in self.connection.AllianceStream(alliance.Response()):
            if request.client != "orchestrator":
                continue
            print("Received GLOBALMODEL from {} ".format(str(request.command), str(request.client)))
            if request.command == alliance.Request.GLOBALMODEL:
                import json
                #print("trying to decode PAYLOAD: {} ".format(request.payload))
                payload = request.payload.replace("\'", "\"")
                payload = json.loads(payload)
                model_id = payload['model_id']
                return self.repository.get_artifact(model_id)

    def set_model(self, model):
        import uuid
        model_id = uuid.uuid4()
        # TODO: Check that this call succeeds
        self.repository.set_artifact(self.bucket_name, str(model_id), model)
        return str(model_id)

    def send_model(self, model_id, to_clients=["orchestrator"]):
        """ Send a message to a client that a model update with model_id is available. 
            Set to empty string to broadcast to all active clients. """

        request = alliance.Request()
        request.command = alliance.Request.MODEL
        payload = {'model_id': str(model_id)}
        request.payload = str(payload)
        request.client = self.client

        for client in to_clients:
            request.to_client=client
            print("RUNTIME: Sending model with id {} to_client {}".format(model_id,client))
            response = self.connection.SendRequest(request)
            print("RUNTIME: ", response.response)

    def _list_clients(self):
        clients = self.connection.ListClients(alliance.Request())
        return clients.client

    def get_active_members(self):
        members = self._list_clients()
        return members

    def nr_active_members(self):
        members = self._list_clients()
        return len(members)

    def _send_heartbeat(self):
        status = alliance.Status()
        status.client = self.client
        status.status = "HEARTBEAT"
        response = self.connection.SendStatus(status) 

    def send_evaluation(self, evaluation="",to_clients=["orchestrator"]):

        request = alliance.Request()
        request.command = alliance.Request.SCORE
        request.payload = str(evaluation)
        request.client = self.client

        for client in to_clients:
            request.to_client=client
            print("sending evaluation to_client {}".format(client))
            self.connection.SendRequest(request)


class MemberRuntimeClient(AllianceRuntimeClient):

    def __init__(self):

        super(MemberRuntimeClient, self).__init__()

        #self.runtime = runtime
        #self.dispatcher = Dispatcher(self.runtime)
        self.dispatcher = Dispatcher(self)
        threading.Thread(target=self.__listen, daemon=True).start()

    def __listen(self):
        # TODO: This is an ugly hack to pass the client name to the server.
        # Should be handled by auth when that is in place. 
        r = alliance.Response()
        r.client = self.client 

        for request in self.connection.AllianceStream(r):
            if request.client == self.client:
                continue
            print("Received {} from {} ".format(str(request.command), str(request.client)))

            status = alliance.Status()
            status.client = self.client
            # Request command types are defined in scaleout.proto.alliance.proto
            # Additional message types can be extended by adding additional alternatives to enum.
            if request.command == alliance.Request.TRAIN:  
                # Train a model according to procedure specified in training code / project.yaml
                model_id = request.payload
                status.status = "Client {0} TRAINING model {1}".format(self.client, model_id)
                self.connection.SendStatus(status)
                model_id = request.payload
                self.__process_training_request(model_id)
                status.status = "Client {0} COMPLETED update of model {1}".format(self.client, model_id)
                self.connection.SendStatus(status)
            elif request.command == alliance.Request.VALIDATE:  # VALIDATING COMMAND
                model_id = request.payload
                status.status = "Client {0} VALIDATING model {1}".format(self.client, model_id)
                self.connection.SendStatus(status)
                self.__process_validation_request(model_id)
            elif request.command == alliance.Request.HEARTBEAT:
                self._send_heartbeat()
            else:
                status.status = "CONNECTING!"
                
            status = alliance.Status()
            status.client = self.client
            status.status = "DONE!"
            self.connection.SendStatus(status)

    def __process_training_request(self,model_id):
        print("Processing training request for model_id {}".format(model_id))
        model = self.get_model(model_id)

        # TODO: use temp-files
        with open("tempin.pyb","wb") as fh:
            fh.write(pickle.dumps(model))

        self.dispatcher.run_cmd('train tempin.pyb tempout.pyb')

        with open("tempout.pyb","rb") as fh:
            model = pickle.loads(fh.read())

        model_id = self.set_model(model)
        self.send_model(model_id)

    def __process_validation_request(self,model_id):
        print("Processing validation request for model_id {}".format(model_id))
        model = self.get_model(model_id)

        # TODO: use temp-files
        with open("tempin.pyb","wb") as fh:
            fh.write(pickle.dumps(model))

        self.dispatcher.run_cmd('validate tempin.pyb tempout.json')

        with open("tempout.json","r") as fh:
            report= json.loads(fh.read())
        report['model_id'] = model_id
        self.send_evaluation(json.dumps(report))


    def send_command(self, cmd):
        request = alliance.Request()
        status = alliance.Status()
        if cmd == "TRAIN":
            request.command = alliance.Request.TRAIN
            status.status = cmd
        elif cmd == "VALIDATE":
            request.command = alliance.Request.VALIDATE
            status.status = cmd
        else:
            request.command = alliance.Request.CONNECT
            status.status = cmd

        status.client = self.client
        request.client = self.client
        print("Sending command {} from {}".format(request.command, request.client))
        self.connection.SendRequest(request)
        self.connection.SendStatus(status)

    def run(self):
        try:
            while True:
                time.sleep(1)
                self._send_heartbeat()
        except KeyboardInterrupt:
            print("ok exiting..")

class OrchestratorRuntimeClient(AllianceRuntimeClient):

    def __init__(self, orchestrator):
        super(OrchestratorRuntimeClient, self).__init__()

        self.orchestrator = orchestrator
        threading.Thread(target=self.__listen, daemon=True).start()

    def __listen(self):

        # TODO: use metadata instead, we now choose channel to listen to via this message.
        r = alliance.Response()
        r.client = self.client 

        for request in self.connection.AllianceStream(r):
            if request.client == self.client:
                continue
            print("Received {} from {} ".format(str(request.command), str(request.client)))

            # Request command types are defined in scaleout.proto.alliance.proto
            # Additional message types can be extended by adding additional alternatives to enum.
            # TODO send as response instead of command
            if request.command == alliance.Request.GLOBALMODEL:
                # A client requests the id of the latest global model
                response = alliance.Request()
                response.command = alliance.Request.GLOBALMODEL
                payload = {'model_id': str(self.orchestrator.get_global_model_id())}
                response.payload = str(payload)
                response.client = self.client
                response.to_client = request.client
                self.connection.SendRequest(response)

            if request.command == alliance.Request.MODEL:
                import json
                payload = request.payload.replace("\'", "\"")
                #print("DEBUG PAYLOAD {}".format(payload))
                try:
                    payload = json.loads(payload)
                    print("ORCHESTRATOR: received MODEL with ID {0} from {1}".format(payload['model_id'],request.client))

                    # Callback implemented in Orchestrator
                    self.orchestrator.receive_model_candidate(payload['model_id'])
                except json.decoder.JSONDecodeError as e:
                    print("No payload available")

            if request.command == alliance.Request.SCORE:
                print("ORCHESTRATOR: received EVALUATION from {}".format(request.client))
                import json
                payload = request.payload.replace("\'", "\"")
                payload = json.loads(payload)
                # return payload to function
                self.orchestrator.receive_validation(payload)


    def request_training_contribution(self, from_clients=[]):
        """ Ask members in from_clients list to train a local model update. """

        request = alliance.Request()
        request.command = alliance.Request.TRAIN
        request.client = self.client
        request.payload = self.orchestrator.get_global_model_id()
        if from_clients == []:
            # Broadcast request to all active member clients
            request.to_client = "" 
            self.connection.SendRequest(request)
        else:
            # Send to all specified clients
            for client in from_clients:
                request.to_client=client
                self.connection.SendRequest(request)
        
        # TODO, send status / INFO msg instead    
        print("ORCHESTRATOR: Sent request_contribution for model {}".format(request.payload))

    def request_validation_contribution(self, model_id, from_clients=[]):
        """ Send a request for members in from_client to validate the model <model_id>. 
            The default is to broadcast the request to all active members. 
        """
        request = alliance.Request()
        request.command = alliance.Request.VALIDATE
        request.payload = model_id
        request.client = self.client

        if from_clients == []:
            request.to_client = "" # Broadcast request to all active member clients
            self.connection.SendRequest(request)
        else:
            # Send to specified clients
            for client in from_clients:
                request.to_client=client
                self.connection.SendRequest(request)

        # TODO: Logging, send info/status message
        print("ORCHESTRATOR: Sent request_validation for model {}".format(request.payload))

    def run(self):
        try:
            while True:
                time.sleep(1)
                self._send_heartbeat()

        except KeyboardInterrupt:
            print("ok exiting..")

