from django.conf import settings
from django.utils.text import slugify
from .exceptions import ModelDeploymentException
from pprint import pprint
from string import Template
import requests
from .models import DeploymentDefinition, DeploymentInstance

DEPLOY_DEFAULT_TEMPLATE = """apiVersion: openfaas.com/v1
kind: Function
metadata:
  name: {name}
  namespace: stack-fn
spec:
  name: {name}
  image: functions/figlet:latest"""

DEPLOY_DEFINITION_TEMPLATE = '''apiVersion: batch/v1
kind: Job
metadata:
  name: build-deploy-definition-$name-$jobid
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: build-depdef
        image: gcr.io/kaniko-project/executor:latest
        args: [ "--dockerfile=Dockerfile",
                "--context=s3://$bucket/$context",
                "--destination=$image"]
        volumeMounts:
          - name: kaniko-secret
            mountPath: /kaniko/.docker
        env:
            - name: AWS_ACCESS_KEY_ID
              value: $access_key
            - name: AWS_SECRET_ACCESS_KEY
              value: $secret_key
            - name: AWS_REGION
              value: us-east-1
            - name: S3_ENDPOINT
              value: $s3endpoint
            - name: S3_FORCE_PATH_STYLE
              value: "true"
      volumes:
        - name: kaniko-secret
          secret:
            secretName: regcred
            items:
              - key: .dockerconfigjson
                path: config.json'''

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

def build_definition(instance):
    import uuid
    build_templ = Template(DEPLOY_DEFINITION_TEMPLATE)
    job = build_templ.substitute(bucket=instance.bucket,
                                 context=instance.filename,
                                 name=instance.name,
                                 jobid=uuid.uuid1().hex,
                                 image='{}.default.svc.cluster.local:5000/depdef-{}'.format(settings.REGISTRY_SVC, instance.name),
                                 access_key=instance.project.project_key,
                                 secret_key=instance.project.project_secret,
                                 s3endpoint='http://{}-minio:9000'.format(instance.project.slug))
    import yaml
    from projects.jobs import start_job
    job = yaml.safe_load(job)
    start_job(job)

# def deploy_model(instance):

#     model = instance.model

#     model_file = model.uid
#     model_bucket = 'models'
    
#     deployment_name = slugify(model.name)
#     deployment_version = model.tag
#     deployment_endpoint = '{}-{}.{}'.format(model.name,
#                                             model.tag,
#                                             settings.DOMAIN)
#     instance.endpoint = deployment_endpoint
    

#     context = instance.deployment
#     context_image = 'registry.{}/depdef-{}'.format(settings.DOMAIN, context.name)

#     project = model.project
#     project_slug = project.slug
#     minio_access_key = project.project_key
#     minio_secret_key = project.project_secret
#     minio_host = project_slug+'-minio:9000'

#     global_domain = settings.DOMAIN

#     parameters = {'release': str(project_slug)+'-'
#                             +str(deployment_name)+'-'
#                             +str(deployment_version),
#                   'chart': 'deploy',
#                   'global.domain': global_domain,
#                   'project.slug': project_slug,
#                   'deployment.version': deployment_version,
#                   'deployment.name': deployment_name,
#                   'deployment.endpoint': deployment_endpoint,
#                   'context.image': context_image,
#                   'model.bucket': model_bucket,
#                   'model.file': model_file,
#                   'minio.host': minio_host,
#                   'minio.secret_key': minio_secret_key,
#                   'minio.access_key': minio_access_key}

#     url = settings.CHART_CONTROLLER_URL + '/deploy'
#     retval = requests.get(url, parameters)
    
#     if retval.status_code >= 200 or retval.status_code < 205:
#         instance.release = parameters['release']
#         # try:
#         #     instance.release = parameters['release']
#         #     instance.save()
#         # except Exception as e:
#         #     print('Failed to save deployment instance.')
#         #     print(e)
#         #     return False
        
#         try:
#             model.status = 'DP'
#             model.save()
#         except Exception as e:
#             print('Failed to update model object.')
#             print(e)
#             return False
#         return True
#     else:
#         print('Failed to launch deploy job.')
#         return False

#     raise ModelDeploymentException(__name__)
