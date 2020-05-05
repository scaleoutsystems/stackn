from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.text import slugify

import requests

class DeploymentDefinition(models.Model):
    project = models.ForeignKey('projects.Project',
                                on_delete=models.DO_NOTHING,
                                related_name='project_owner')
    name = models.CharField(max_length=512, unique=True)
    bucket = models.CharField(max_length=512)
    filename = models.CharField(max_length=512)
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

    deployment = models.ForeignKey('deployments.DeploymentDefinition', on_delete=models.DO_NOTHING)

    model = models.OneToOneField('models.Model', on_delete=models.DO_NOTHING, related_name='deployed_model', unique=True)
    access = models.CharField(max_length=2, choices=ACCESS, default=PRIVATE)
    endpoint = models.CharField(max_length=512)
    release = models.CharField(max_length=512)
    # sample_input = models.TextField(blank=True, null=True)
    # sample_output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}:{}".format(self.model.name, self.model.tag)

@receiver(pre_delete, sender=DeploymentInstance, dispatch_uid='deployment_pre_delete_signal')
def pre_delete_deployment(sender, instance, using, **kwargs):
    import requests
    parameters = {'release': instance.release}
    url = settings.CHART_CONTROLLER_URL + '/delete'
    retval = requests.get(url, parameters)
    if retval.status_code >= 200 or retval.status_code < 205:
        model = instance.model
        model.status = 'CR'
        model.save()

@receiver(pre_save, sender=DeploymentInstance, dispatch_uid='deployment_pre_save_signal')
def pre_save_deployment(sender, instance, using, **kwargs):
    model = instance.model

    if model.status == 'DP':
        raise Exception('Model already deployed.')

    model_file = model.uid
    model_bucket = 'models'
    
    deployment_name = slugify(model.name)
    deployment_version = model.tag
    deployment_endpoint = '{}-{}.{}'.format(model.name,
                                            model.tag,
                                            settings.DOMAIN)
    instance.endpoint = deployment_endpoint
    

    context = instance.deployment
    context_image = 'registry.{}/depdef-{}'.format(settings.DOMAIN, context.name)

    project = model.project
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
                  'deployment.endpoint': deployment_endpoint,
                  'context.image': context_image,
                  'model.bucket': model_bucket,
                  'model.file': model_file,
                  'minio.host': minio_host,
                  'minio.secret_key': minio_secret_key,
                  'minio.access_key': minio_access_key}

    url = settings.CHART_CONTROLLER_URL + '/deploy'
    retval = requests.get(url, parameters)
    
    if retval.status_code >= 200 or retval.status_code < 205:
        instance.release = parameters['release']
        model.status = 'DP'
        model.save()
    else:
        raise Exception('Failed to launch deploy job.')

