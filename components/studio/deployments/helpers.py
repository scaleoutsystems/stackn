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
  name: bld-depdef-$name-$jobid
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
    from projects.helpers import get_minio_keys

    minio_keys = get_minio_keys(instance.project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']

    build_templ = Template(DEPLOY_DEFINITION_TEMPLATE)
    image = 'registry.{}/depdef-{}'.format(settings.DOMAIN, instance.name)
    job = build_templ.substitute(bucket=instance.bucket,
                                 context=instance.filename,
                                 name=instance.name,
                                 jobid=uuid.uuid1().hex[0:5],
                                 image='{}.default.svc.cluster.local:5000/depdef-{}'.format(settings.REGISTRY_SVC, instance.name),
                                 access_key=decrypted_key,
                                 secret_key=decrypted_secret,
                                 s3endpoint='http://{}-minio:9000'.format(instance.project.slug))
    import yaml
    from projects.jobs import start_job
    job = yaml.safe_load(job)
    start_job(job)
    instance.image = image
    instance.save()
