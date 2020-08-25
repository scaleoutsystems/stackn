from django.db import models
from django.db.models.signals import pre_delete, pre_save
from deployments.models import HelmResource
from django.dispatch import receiver
import uuid


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
    parameters = {
        "release": release_name,
        "chart": "cronjob",
        "project.slug": instance.project.slug,
        "image": instance.environment.image,
        "command": str(instance.command.split(' ')),
        "cronjob.schedule": instance.schedule,
        "cronjob.port": "8786",
        "resources.limits.cpu": "500m",
        "resources.limits.memory": "1Gi",
        "resources.requests.cpu": "100m",
        "resources.requests.memory": "256Gi"
    }
    helmchart = HelmResource(name=release_name,
                             namespace='Default',
                             chart='cronjob',
                             params=parameters,
                             username=instance.username)
    helmchart.save()
    instance.helmchart = helmchart
