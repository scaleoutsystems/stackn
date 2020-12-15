from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.conf import settings
from rest_framework.renderers import JSONRenderer
from deployments.models import HelmResource
from django.dispatch import receiver
import uuid
import json
import yaml

from labs.helpers import create_user_settings


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=512)
    command = models.CharField(max_length=1024)
    environment = models.ForeignKey('projects.Environment', on_delete=models.CASCADE, related_name='job_environment')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='job_project')
    schedule = models.CharField(max_length=128)
    helmchart = models.OneToOneField('deployments.HelmResource', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

@receiver(pre_save, sender=Experiment, dispatch_uid='experiment_pre_save_signal')
def pre_save_experiments(sender, instance, using, **kwargs):
    print('creating cronjob chart')
    job_id = uuid.uuid1().hex[0:5]
    release_name = '{}-{}-{}'.format(instance.project.slug, 'cronjob', job_id)
    is_cron = 1
    if instance.schedule == "None" or instance.schedule == "":
        is_cron = 0

    from api.serializers import ProjectSerializer
    settings_file = ProjectSerializer(instance.project)

    settings_file = JSONRenderer().render(settings_file.data)
    settings_file = settings_file.decode('utf-8')

    settings_file = json.loads(settings_file)
    settings_file = yaml.dump(settings_file)

    user_config_file = create_user_settings(instance.username)
    user_config_file = yaml.dump(json.loads(user_config_file))

    parameters = {
        "release": release_name,
        "chart": "cronjob",
        "namespace": settings.NAMESPACE,
        "project.slug": instance.project.slug,
        "image": instance.environment.image,
        "command": '["/bin/bash", "-c", "'+instance.command+'"]',
        "iscron": str(is_cron),
        "cronjob.schedule": instance.schedule,
        "cronjob.port": "8786",
        "resources.limits.cpu": "500m",
        "resources.limits.memory": "1Gi",
        "resources.requests.cpu": "100m",
        "resources.requests.memory": "256Mi",
        "resources.gpu.enabled": "false",
        "settings_file": settings_file,
        "user_settings_file": user_config_file,
    }
    if hasattr(instance, 'options'):
        del instance.options['command']
        del instance.options['environment']
        del instance.options['schedule']
        parameters.update(instance.options)
    helmchart = HelmResource(name=release_name,
                             namespace='Default',
                             chart='cronjob',
                             params=parameters,
                             username=instance.username)
    helmchart.save()
    instance.helmchart = helmchart
