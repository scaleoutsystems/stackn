from django.conf import settings
from pprint import pprint

DEPLOY_DEFAULT_TEMPLATE = """apiVersion: openfaas.com/v1
kind: Function
metadata:
  name: {name}
  namespace: stack-fn
spec:
  name: {name}
  image: functions/figlet:latest"""


def get_instance_from_definition(instance):
    ret = None

    if instance.deployment:
        ret = str(instance.deployment.definition)
    else:
        ret = str(DEPLOY_DEFAULT_TEMPLATE)

    # Replace deployment definition template fields with model instance variables.
    ret = ret.format(name=instance.name)

    import yaml
    ret = yaml.safe_load(ret)

    return ret


def deploy_model(instance):

    print("deploying model with {}!".format(instance))

    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.CustomObjectsApi()

    yaml_definition = get_instance_from_definition(instance)

    # create the resource
    api.create_namespaced_custom_object(
        group="openfaas.com",
        version="v1",
        namespace="stack-fn",
        plural="functions",
        body=yaml_definition,
    )
    print("Resource created")

    # get the resource and print out data
    resource = api.list_namespaced_custom_object(
        group="openfaas.com",
        version="v1",
        namespace="stack-fn",
        plural="functions",
    )
    print("Resources details:")
    pprint(resource)


def undeploy_model(instance):
    #instance.model.status = instance.model.CREATED
    #instance.model.url = ''
    #instance.model.save()

    from kubernetes import client, config
    import yaml

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.CustomObjectsApi()

    api.delete_namespaced_custom_object(
        group="openfaas.com",
        version="v1",
        name=str(instance.name),
        namespace="stack-fn",
        plural="functions",
        body=client.V1DeleteOptions(),
    )
    print("Resource deleted")

