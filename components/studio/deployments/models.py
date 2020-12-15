from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.text import slugify
import yaml
import json
from projects.helpers import get_minio_keys
import os
import requests
import modules.keycloak_lib as keylib

class HelmResource(models.Model):
    name = models.CharField(max_length=512, unique=True)
    namespace = models.CharField(max_length=512)
    chart = models.CharField(max_length=512)
    params = models.CharField(max_length=10000)
    username = models.CharField(max_length=512)
    status = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "{}".format(self.name)

@receiver(pre_save, sender=HelmResource, dispatch_uid='helmresource_pre_save_signal')
def pre_save_helmresource(sender, instance, using, **kwargs):
    update = HelmResource.objects.filter(name=instance.name)
    action = 'deploy'
    if update:
        action = 'upgrade'
    url = settings.CHART_CONTROLLER_URL + '/'+action
    print(instance.params)
    retval = requests.get(url, instance.params)
    if retval:
        print('Resource: '+instance.name)
        print('Action: '+action)
        instance.status = 'OK'
    else:
        print('Failed to deploy resource: '+instance.name)
        print('Reason: {}'.format(retval.text))
        print('Status code: {}'.format(retval.status_code))
        instance.status = 'Failed'

@receiver(pre_delete, sender=HelmResource, dispatch_uid='helmresource_pre_delete_signal')
def pre_delete_helmresource(sender, instance, using, **kwargs):
    print('Deleting helm resource.')
    if instance.status == 'OK':
        parameters = {'release': instance.name}
        url = settings.CHART_CONTROLLER_URL + '/delete'
        retval = requests.get(url, parameters)
        if retval:
            print('Deleted resource: '+instance.name)
        else:
            print('Failed to delete resource: '+instance.name)

class DeploymentDefinition(models.Model):

    PRIVATE = 'PR'
    PUBLIC = 'PU'
    ACCESS = [
        (PRIVATE, 'Private'),
        (PUBLIC, 'Public'),
    ]

    project = models.ForeignKey('projects.Project',
                                on_delete=models.CASCADE,
                                related_name='project_owner', blank=True, null=True)
    access = models.CharField(max_length=2, choices=ACCESS, default=PRIVATE)
    name = models.CharField(max_length=512, unique=True)
    bucket = models.CharField(max_length=512, blank=True, null=True)
    filename = models.CharField(max_length=512, blank=True, null=True)
    image = models.CharField(max_length=512, blank=True, null=True)
    path_predict = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}".format(self.name)

class DeploymentInstance(models.Model):


    PRIVATE = 'PR'
    LIMITED = 'LI'
    PUBLIC = 'PU'
    ACCESS = [
        (PRIVATE, 'Private'),
        (LIMITED, 'Limited'),
        (PUBLIC, 'Public'),
    ]

    deployment = models.ForeignKey('deployments.DeploymentDefinition', on_delete=models.CASCADE)
    appname = models.CharField(max_length=512)
    model = models.OneToOneField('models.Model', on_delete=models.CASCADE, related_name='deployed_model', unique=True)
    access = models.CharField(max_length=2, choices=ACCESS, default=PRIVATE)
    endpoint = models.CharField(max_length=512)
    path = models.CharField(max_length=512)
    release = models.CharField(max_length=512)
    helmchart = models.OneToOneField('deployments.HelmResource', on_delete=models.CASCADE)
    created_by = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}:{}".format(self.model.name, self.model.version)

@receiver(pre_delete, sender=DeploymentInstance, dispatch_uid='deployment_pre_delete_signal')
def pre_delete_deployment(sender, instance, using, **kwargs):

    model = instance.model
    model.status = 'CR'
    model.save()
    # Uninstall resources
    # chart = instance.helmchart
    # chart.delete()
    # Clean up in Keycloak
    print('Cleaning up in Keycloak...')
    kc = keylib.keycloak_init()
    keylib.keycloak_delete_client(kc, instance.release) 
    scope_id = keylib.keycloak_get_client_scope_id(kc, instance.release+'-scope')
    keylib.keycloak_delete_client_scope(kc, scope_id)
    print('Done.')

@receiver(pre_save, sender=DeploymentInstance, dispatch_uid='deployment_pre_save_signal')
def pre_save_deployment(sender, instance, using, **kwargs):
    model = instance.model

    if model.status == 'DP':
        raise Exception('Model already deployed.')

    model_file = model.uid
    model_bucket = 'models'
    
    deployment_name = slugify(model.name)
    deployment_version = slugify(model.version)
    deployment_endpoint = '{}-{}.{}'.format(model.name,
                                            model.version,
                                            settings.DOMAIN) 
    
    deployment_endpoint = settings.DOMAIN
    deployment_path = '/{}/serve/{}/{}/'.format(model.project.slug,
                                               slugify(model.name),
                                               slugify(model.version))

    instance.endpoint = deployment_endpoint
    instance.path = deployment_path

    context = instance.deployment
    context_image = context.image

    project = model.project
    project_slug = project.slug

    minio_keys = get_minio_keys(project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']
    minio_access_key = decrypted_key
    minio_secret_key = decrypted_secret

    minio_host = project_slug+'-minio:9000'

    global_domain = settings.DOMAIN

    
    HOST = settings.DOMAIN
    RELEASE_NAME = slugify(str(project_slug)+'-'+str(deployment_name)+'-'+str(deployment_version))
    burl = os.path.join('https://', HOST)
    eurl = os.path.join(deployment_endpoint, deployment_path)
    URL = burl+eurl
 
    
    instance.appname =instance.model.project.slug+'-'+slugify(instance.model.name)+'-'+slugify(instance.model.version)
    
    # Create Keycloak client corresponding to this deployment
    client_id, client_secret = keylib.keycloak_setup_base_client(URL, RELEASE_NAME, instance.created_by, ['owner'], ['owner'])
    
    skip_tls = 0
    if not settings.OIDC_VERIFY_SSL:
        skip_tls = 1
        print("WARNING: Skipping TLS verify.")

    
    # Default is that access is private.
    rules = """resources:
    - uri: /*
      roles:
      - {}:owner
    """.format(client_id)

    access_rules = {"gatekeeper.rules": rules}

    if 'access' in instance.params:
        print(instance.params['access'])
        if instance.params['access'] == 'public':
            print("Public endpoint")
            access_rules = {"gatekeeper.rules": "public"}
        del instance.params['access']

    envstr = []
    envparams = []

    if 'environment' in instance.params:
        envvars = instance.params['environment']
        envstr = ""
        for envvar in envvars:
            envstr += """
- name: {}
  value: {}          
            """.format(envvar['name'], envvar['value'])
        print(envstr)
        del instance.params['environment']

    if envstr:
        envparams = {"extraEnv": envstr}        

    parameters = {'release': RELEASE_NAME,
                  'chart': 'deploy',
                  'namespace': settings.NAMESPACE,
                  'appname': instance.appname,
                  'replicas': '1',
                  'global.domain': global_domain,
                  'project.slug': project_slug,
                  'deployment.version': deployment_version,
                  'deployment.name': deployment_name,
                  'deployment.endpoint': deployment_endpoint,
                  'deployment.path': deployment_path,
                  'context.image': context_image,
                  'model.bucket': model_bucket,
                  'model.file': model_file,
                  'minio.host': minio_host,
                  'minio.secret_key': minio_secret_key,
                  'minio.access_key': minio_access_key,
                  'gatekeeper.realm': settings.KC_REALM,
                  'gatekeeper.client_secret': client_secret,
                  'gatekeeper.client_id': client_id,
                  'gatekeeper.auth_endpoint': settings.OIDC_OP_REALM_AUTH,
                  'gatekeeper.skip_tls': str(skip_tls)}
    param_success = True
    try:
        parameters.update(instance.params)
        parameters.update(access_rules)
        if envparams:
            parameters.update(envparams)
        
        if 'minio.buckets' in instance.params:
            bucket_param = '{'
            buckets = instance.params['minio.buckets']
            for bucket in buckets:
                bucket_param += bucket+','
            bucket_param = bucket_param[0:-1]+'}'
            del instance.params['minio.buckets']
            parameters.update({"minio.buckets": bucket_param})
      except:
          print("Failed to update parameters in deployment.models")
          param_success = False
    
    print('creating chart')
    helmchart = HelmResource(name=RELEASE_NAME,
                             namespace='Default',
                             chart='deploy',
                             params=parameters,
                             username=instance.created_by)
    helmchart.save()
    instance.helmchart = helmchart

    if helmchart.status == 'Failed' or (not param_success):
        # If fail, clean up in Keycloak
        kc = keylib.keycloak_init()
        keylib.keycloak_delete_client(kc, RELEASE_NAME) 
        scope_id = keylib.keycloak_get_client_scope_id(kc, RELEASE_NAME+'-scope')
        keylib.keycloak_delete_client_scope(kc, scope_id)
        raise Exception('Failed to launch deploy job.')
    else:
        instance.release = RELEASE_NAME
        model.status = 'DP'
        model.save()