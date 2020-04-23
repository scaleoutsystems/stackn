from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging

logger = logging.getLogger(__file__)

class Deployer(object):

    __config = None

    @staticmethod
    def __resolve_namespace(definition):
        try:
            namespace = definition['metadata']['namespace']
        except KeyError as e:
            namespace = 'default'
        return namespace

    @staticmethod
    def __resolve_namespace_and_name(definition):
        try:
            namespace = str(definition['metadata']['namespace'])
        except KeyError as e:
            namespace = 'default'
        try:
            name = str(definition['metadata']['name'])
        except KeyError as e:
            name = None
        return name, namespace

    def __init__(self):
        import os
        path = os.getcwd()
        # config.load_kube_config('cluster.conf')
        config.load_kube_config(config_file=path + '/cluster.conf')
        self.pretty = True
        self.logger = logging.getLogger(__name__)

    def deploy(self, definition):
        if definition['kind'] == 'PersistentVolumeClaim':
            self.create_pvc(definition)
        elif definition['kind'] == 'Ingress':
            self.create_ingress(definition)
        elif definition['kind'] == 'Deployment':
            self.create_deployment(definition)
        elif definition['kind'] == 'Service':
            self.create_service(definition)
        else:
            self.logger.error("{} NYI".format(__file__))

    def scale(self, definition, scale):
        if definition['kind'] == 'Deployment':
            self.apply_deployment(definition, scale)
        else:
            self.logger.error("{} NYI".format(__file__))

    def delete(self, definition):
        if definition['kind'] == 'PersistentVolumeClaim':
            self.delete_pvc(definition)
        elif definition['kind'] == 'Ingress':
            self.delete_ingress(definition)
        elif definition['kind'] == 'Deployment':
            self.delete_deployment(definition)
        elif definition['kind'] == 'Service':
            self.delete_service(definition)
        else:
            self.logger.error("{} NYI".format(__file__))

    def create_pvc(self, definition):
        namespace = self.__resolve_namespace(definition)

        api = client.CoreV1Api()
        try:
            api_response = api.create_namespaced_persistent_volume_claim(namespace, definition, pretty=self.pretty)
            self.logger.info("Persistent Volume Claim created. status='%s'" % api_response.metadata.name)
        except ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->create_namespaced_persistent_volume_claim: %s\n" % e)

    def create_ingress(self, definition):
        namespace = self.__resolve_namespace(definition)

        api = client.NetworkingV1beta1Api()
        try:
            api_response = api.create_namespaced_ingress(namespace, definition, pretty=self.pretty)
            self.logger.info("Ingress created. status='%s'" % api_response.metadata.name)
        except ApiException as e:
            self.logger.error("Exception when calling ExtensionsV1beta1Api->create_namespaced_ingress: %s\n" % e)

    def create_deployment(self, definition):
        namespace = self.__resolve_namespace(definition)
        api = client.AppsV1Api()
        try:
            api_response = api.create_namespaced_deployment(namespace, definition, pretty=self.pretty)
            self.logger.info("Deployment created. status='%s'" % api_response.metadata.name)
        except ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->create_namespaced_deployment: %s\n" % e)

    def create_service(self, definition):
        namespace = self.__resolve_namespace(definition)
        api = client.CoreV1Api()
        try:
            api_response = api.create_namespaced_service(namespace, definition, pretty=self.pretty)
            self.logger.info("Service created. status='%s'" % api_response.metadata.name)
            # pprint(api_response)
        except ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->create_namespaced_service: %s\n" % e)

    def apply_deployment(self, definition, scale=1):
        namespace = self.__resolve_namespace(definition)
        definition['spec']['replicas'] = str(scale)
        api = client.AppsV1Api()
        try:
            api_response = api.patch_namespaced_deployment(namespace, definition, pretty=self.pretty)
            self.logger.info("Deployment patched. status='%s'" % api_response.metadata.name)
        except ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->patch_namespaced_deployment: %s\n" % e)

    def delete_pvc(self, definition):
        name, namespace = self.__resolve_namespace_and_name(definition)
        api = client.CoreV1Api()
        try:
            api_response = api.delete_namespaced_persistent_volume_claim(name, namespace, pretty=self.pretty)
            self.logger.info("Persistent Volume Claim deleted. status='%s'" % api_response.metadata.name)
        except ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->delete_namespaced_persistent_volume_claim: %s\n" % e)

    def delete_ingress(self, definition):
        name, namespace = self.__resolve_namespace_and_name(definition)
        api = client.NetworkingV1beta1Api()
        try:
            api_response = api.delete_namespaced_ingress(name, namespace, pretty=self.pretty)
            self.logger.info("Ingress deleted. status='%s'" % api_response.metadata.name)
        except ApiException as e:
            self.logger.error("Exception when calling ExtensionsV1beta1Api->delete_namespaced_ingress: %s\n" % e)

    def delete_deployment(self, definition):
        name, namespace = self.__resolve_namespace_and_name(definition)
        api = client.AppsV1Api()
        try:
            api_response = api.delete_namespaced_deployment(name, namespace, pretty=self.pretty)
            self.logger.info("Deployment deleted. status='%s'" % api_response.metadata.name)
        except ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->delete_namespaced_deployment: %s\n" % e)

    def delete_service(self, definition):
        name, namespace = self.__resolve_namespace_and_name(definition)
        api = client.CoreV1Api()
        try:
            api_response = api.delete_namespaced_service(name, namespace, pretty=self.pretty)
            self.logger.info("Service deleted. status='%s'" % api_response.metadata.name)
            # pprint(api_response)
        except ApiException as e:
            self.logger.error("Exception when calling CoreV1Api->delete_namespaced_service: %s\n" % e)

