import os
from scaleout.config.config import load_config as load_conf, get_default_config_file_path

from scaleout.runtime.runtime import Runtime

from scaleout.auth import get_bearer_token
from scaleout.errors import AuthenticationError

import requests
import json
import pickle
from slugify import slugify
import uuid


def _check_status(r,error_msg="Failed"):
    if (r.status_code < 200 or r.status_code > 299):
        print(error_msg)
        print('Returned status code: {}'.format(r.status_code))
        print('Reason: {}'.format(r.reason))
        print(r.text)
        return False
    else:
        return True 


class StudioClient(Runtime):

    def __init__(self, config=None, login=True, endpoints=True):
        super(StudioClient, self).__init__()


        self.username = self.config['username']
        self.password = self.config['password']
        self.project_name = self.config['Project']['project_name']
        self.auth_url = self.config['auth_url']
        self.global_domain = self.config['so_domain_name']
        # TODO: This assumes a certain url-schema
        self.api_url = self.auth_url.replace("/api-token-auth",'')

        # Connect requests and sets an auth token (unique to this session)
        self.login = login
        if self.login:
            self.connect()
            self.auth_headers = {'Authorization': 'Token {}'.format(self.token)}
        else:
            self.auth_headers = None

        # Fetch and set all active API endpoints
        if endpoints:
            self.get_endpoints()

        self.project = self.get_project(self.project_name)
        if not self.project:
            print('Did not find project: {}'.format(self.project_name))
            self.project_id = None
        else:
            self.project_id = self.project['id']
            self.project_slug = self.project['slug']
            self.project_id = self.project['id']

    def get_endpoints(self):
        endpoints = self.list_endpoints()
        self.endpoints = endpoints
        self.models_api = endpoints['models']
        self.reports_api = endpoints['reports']
        self.projects_api = endpoints['projects']
        self.generators_api = endpoints['generators']
        self.deployment_instance_api = endpoints['deploymentInstances']
        self.deployment_definition_api = endpoints['deploymentDefinitions']


    def connect(self):
        """ Fetch and set an API bearer token """ 
        url = self.config['auth_url']
        try:
            self.token = get_bearer_token(url, self.username, self.password)
        except AuthenticationError:
            self.token=None
            raise

    def _get_repository_conf(self):
        """ Return the project minio keys. """
        #TODO: If we have multiple repositories configured, studio, minio, s3, etc, we 
        # neet to supply repository name.

        project = self.get_project(self.project_name)

        # TODO: Obtain port and host from Studio backend API, this assumes a certain naming schema  
        data = {
            'minio_host': '{}-minio.{}'.format(slugify(self.project_slug),self.config['so_domain_name']),
            'minio_port': 9000,
            'minio_access_key': project['project_key'],
            'minio_secret_key': project['project_secret'],
            'minio_secure_mode': True,
        }
        return data

    def get_repository(self):
        from scaleout.repository.helpers import get_repository as gr
        repository_config = self._get_repository_conf()
        repo = gr(repository_config)
        return repo

    def list_endpoints(self):
        """ List api endpoints """

        # TODO: "studio" subdomain hardcoded here
        #url = "https://studio.{}/api/".format(self.config['so_domain_name'])
        headers = {'Authorization': 'Token {}'.format(self.token)}
        r = requests.get(self.api_url, headers=headers)

        if (r.status_code < 200 or r.status_code > 299):
            print("Endpoint list failed.")
            print('Returned status code: {}'.format(r.status_code))
            print('Reason: {}'.format(r.reason))
            return None
        else:
            return json.loads(r.content)


    ### Projects api  ####

    def list_projects(self):
        """ List all projects a user has access to. """
        url = self.projects_api
        r = requests.get(url, headers=self.auth_headers)
        if (r.status_code < 200 or r.status_code > 299):
            print("List projects failed.")
            print('Returned status code: {}'.format(r.status_code))
            print('Reason: {}'.format(r.reason))
            return None
        else:
            return json.loads(r.content)

    def get_project(self, project_name):
        projects = self.list_projects()
        if not projects:
            return None
        for p in projects:
            if p['name'] == project_name:
                return p

    def create_deployment_definition(self, name, filepath, path_predict=''):

        if filepath[-6:] != 'tar.gz':
            print('Deployment definition should have extension tar.gz')
            return None

        bucket = 'deploy'
        # Create unique file name
        filename = uuid.uuid1().hex+'.tar.gz'
        repo = self.get_repository()
        repo.set_artifact(filename, filepath, is_file=True, bucket=bucket)
        depde_data = {"project": self.project_id,
                      "name": name,
                      "bucket": bucket,
                      "filename": filename,
                      "path_predict": path_predict}

        url = self.deployment_definition_api
        r = requests.post(url, json=depde_data, headers=self.auth_headers)
        status = _check_status(r, error_msg='Failed to create deployment definition')
        if not status:
            repo.delete_artifact(filename, bucket)
            return False

        print('Created deployment definition: {}'.format(name))
        return True
            

    

    def get_deployment_definition(self, name):
        url = os.path.join(self.deployment_definition_api, '?name={}'.format(name))
        r = requests.get(url, headers=self.auth_headers)
        if _check_status(r,error_msg="Get deployment definition failed."):
            return json.loads(r.content)
        else:
            return []

    ### Datasets API ###


    def list_datasets(self):
        # TODO: This only lists datasets in Minio, not the ones in Studio (Django-managed). 
        # We should here use the Studio datasets api when it is available
        from minio.error import NoSuchBucket
        repo = self.get_repository()
        try:
            objs = repo.client.list_objects(bucket_name="dataset")
        except NoSuchBucket as e:
            print("The datasets repository has not been initialized yet.", e)
        return objs


    ### Models API ###

    

    def show_model(self, model_id=None):
        """ Get all metadata associated with a model. """
        try:
            for model in self.list_models():
                if model['uid'] == model_id:
                    return model
        except:
            raise
        
        print("No model found with id: ", model_id)
        return None

    def get_model(self,name):
        """ Return model object and model metadata. """
        url = os.path.join(self.models_api, '?name={}'.format(name))
        r = requests.get(url, headers=self.auth_headers)
        if _check_status(r,error_msg="Get model failed."):
            return json.loads(r.content)
        else:
            return r.status_code

    def delete_model(self,model_name, tag=None):
        """ Delete a model. If tag is none, all tags associated with model_name
        are deleted. If a tag is given, only that tag is deleted.   """

        # TODO: Implement delete in the Studio backend

        # Get all model ids with correct name
        models = self.list_models()
        models_to_delete = []
        for model in models:
            if model["name"] == model_name and (model["tag"]==tag or tag==None):
                models_to_delete.append(model)

        for model in models_to_delete:
            print(models)
            url = self.models_api
            #url = "https://{}/api/models/{}".format(self.config['so_domain_name'],model["id"])
            model_uid = model["uid"]
            r = requests.delete(url,headers=self.auth_headers)
            if _check_status(r,"Failed to delete model: {}".format(model["uid"])):
                # Delete the data in minio
                repo.delete_artifact(model_uid)        

    def create_model(self, instance, model_name, tag='latest', model_description=None,is_file=True):
        """ Publish a model to Studio. """

        # TODO: Support model tagging, default to 'latest'
        import uuid
        model_uid = str(uuid.uuid1().hex)
        repo = self.get_repository()
        repo.bucket = 'models'
        # Upload model.

        repo.set_artifact(model_uid, instance, is_file)
 
        model_data = {"uid": model_uid,
                      "name": model_name,
                      "tag": tag,
                      "description": model_description,
                      "project": str(self.project_id)}

        url = self.models_api
        url = url.replace('http:', 'https:')

        r = requests.post(url, json=model_data, headers=self.auth_headers)
        if not _check_status(r, error_msg="Failed to create model."):
            repo.delete_artifact(model_uid)
            return False

        print('Created model: {}, tag: {}'.format(model_name, tag))
        return True

    def deploy_model(self, model, deploy_context, model_name, version='latest'):
        
        dd = self.get_deployment_definition(deploy_context)
        if dd and ('id' in dd[0]):
            context_id = dd[0]['id']
        else:
            print('Deployment definition {} does not exist.'.format(deploy_context))

        model_obj = self.get_model(model)
        model_id = model_obj[0]['id']

        url = self.deployment_instance_api
        #endpoint = "http://{}-{}.default/v1/models/model:predict".format(model_name, version)
        # endpoint = url+'predict/?name={}&version={}'.format(model_name, version)

        dp_data = {"deployment": context_id,
                   "model": model_id,
                   "name": model_name,
                   "endpoint": 'http://default.com',
                   "version": version}
        
        r = requests.post(url, json=dp_data, headers=self.auth_headers)
        if not _check_status(r, error_msg="Failed to create deployment."):
            return False

        url = self.deployment_instance_api+'build_instance/'
        bd_data = {"name": model_name}
        r = requests.post(url, json=bd_data, headers=self.auth_headers)
        if not _check_status(r, error_msg="Failed to start build process."):
            # Delete registered deployment instance from db
            return False

        print('Created deployment: {}'.format(model_name))
        return True

    
    def create_list(self, resource):
        url = self.endpoints[resource]
        r = requests.get(url, headers=self.auth_headers)
        if not _check_status(r, error_msg="Failed to list {}.".format(resource)):
            return False
        else:
            return json.loads(r.content)


if __name__ == '__main__':

    client = StudioClient()
    p = client.get_project("Test")
    print("Project:", p)
    e = client.list_endpoints()
    print("Endpoints: ", e)
    data = client._get_repository_conf()
    print("Minio settings: ", data)

    print(client.token)
    #objs = client.list_datasets()
    #for obj in objs:
    #    print(obj)

    #import pickle
    #model = "jhfjkshfks"*1000
    #data = pickle.dumps(model)
    #client.publish_model(data,"testmodel",tag="v0.0.1",model_description="A test to check client API functionality.", is_file=False)

    #data = client.list_models()
    #print(data)

    #data = client.show_model(model_id="167d8f0070c611ea96fcf218982f8078")
    #print(data)
