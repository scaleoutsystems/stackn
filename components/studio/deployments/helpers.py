from django.conf import settings
from .exceptions import ModelDeploymentException
from pprint import pprint
import requests
# from .models import DeploymentDefinition
# from models.models import Model
# from projects.models import Project

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

    model = instance.model
    print('got model')

    model_file = model.uid
    model_bucket = 'models'
    
    deployment_name = instance.name
    deployment_version = instance.version
 
    context = instance.deployment
    print('got context')
    context_bucket = context.bucket
    context_file = context.filename

    project = context.project
    print('got project')
    project_slug = project.slug
    minio_access_key = project.project_key
    minio_secret_key = project.project_secret
    minio_host = project_slug+'-minio:9000'

    global_domain = settings.DOMAIN

    parameters = {'release': str(project_slug)+'-'
                            +str(deployment_name)+'-'
                            +str(deployment_version),
                  'chart': 'deploy',
                  'global.domain': global_domain,
                  'project.slug': project_slug,
                  'deployment.version': deployment_version,
                  'deployment.name': deployment_name,
                  'context.bucket': context_bucket,
                  'context.file': context_file,
                  'model.bucket': model_bucket,
                  'model.file': model_file,
                  'minio.host': minio_host,
                  'minio.secret_key': minio_secret_key,
                  'minio.access_key': minio_access_key}
    url = settings.CHART_CONTROLLER_URL + '/deploy'
    print('calling: '+url)
    retval = requests.get(url, parameters)
    
    print("CREATE_MODEL_DEPLOYMENT:helm chart creator returned {}".format(retval))
    if retval.status_code >= 200 or retval.status_code < 205:
        return True

    raise ModelDeploymentException(__name__)

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

