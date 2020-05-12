from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from deployments.models import DeploymentInstance

class Model(models.Model):

    PRIVATE = 'PR'
    LIMITED = 'LI'
    PUBLIC = 'PU'
    ACCESS = [
        (PRIVATE, 'Private'),
        (LIMITED, 'Limited'),
        (PUBLIC, 'Public'),
    ]

    CREATED = 'CR'
    DEPLOYED = 'DP'
    ARCHIVED = 'AR'
    STATUS = [
        (CREATED, 'Created'),
        (DEPLOYED, 'Deployed'),
        (ARCHIVED, 'Archived'),
    ]
    uid = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    access = models.CharField(max_length=2, choices=ACCESS, default=PRIVATE)
    resource = models.URLField(max_length=2048, null=True, blank=True)
    url = models.URLField(max_length=512, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        related_name='model_owner',
        null=True)
    status = models.CharField(max_length=2, choices=STATUS, default=CREATED)
    tag = models.CharField(max_length=10, default='latest')
    
    class Meta:
        unique_together = ('name', 'tag')
    def __str__(self): 
        return "{name}".format(name=self.name)

@receiver(pre_delete, sender=Model, dispatch_uid='model_pre_delete_signal')
def pre_delete_deployment(sender, instance, using, **kwargs):
    # TODO: Also delete model from minio
    # Check if model has been deployed, if so, delete deployment.
    if instance.status == 'DP':
        deployment = DeploymentInstance.objects.get(model=instance)
        deployment.delete()