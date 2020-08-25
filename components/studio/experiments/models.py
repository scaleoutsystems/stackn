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
    helmchart = models.OneToOneField('deployments.HelmResource', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

@receiver(pre_save, sender=Experiment, dispatch_uid='experiment_pre_save_signal')
def pre_save_experiments(sender, instance, using, **kwargs):
    print('creating cronjob chart')
    release_name = '{}-{}-{}'.format(instance.project.slug, 'cronjob', instance.id)
    parameters = {
      
    }
    helmchart = HelmResource(name=release_name,
                             namespace='Default',
                             chart='deploy',
                             params=parameters,
                             username=instance.username)