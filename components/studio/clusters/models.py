from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.text import slugify
import uuid



import modules.keycloak_lib as keylib

class Cluster(models.Model):
    name = models.CharField(max_length=512, unique=True)
    base_url = models.CharField(max_length=512)
    config = models.TextField()
    namespace = models.CharField(max_length=512)
    storageclass = models.CharField(max_length=512, default="microk8s-hostpath")
    status = models.CharField(max_length=30, default="active")
    quota = models.TextField(default="")
    load = models.TextField(default="")
    helmchart_id = models.IntegerField(default=-1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{}".format(self.name)

@receiver(post_save, sender=Cluster, dispatch_uid='cluster_post_save_signal')
def post_save_cluster(sender, instance, **kwargs):
    RELEASE_NAME = slugify(instance.name)+'-stackn-monitor'+'-'+slugify(uuid.uuid4().hex[0:4])
    user = 'admin'
    parameters = {  
                    'release': RELEASE_NAME,
                    'appname': RELEASE_NAME,
                    'chart': 'monitor',
                    'namespace': instance.namespace,
                    'resources_url': settings.STUDIO_HOST+'/api/resources/',
                    'cluster_name': instance.name,
                    'cluster_config': instance.config
                  }

    print("Deploying monitor service")

    from deployments.models import HelmResource
    helmchart = HelmResource(name=RELEASE_NAME,
                             namespace=instance.namespace,
                             chart='monitor',
                             params=parameters,
                             username=user,
                             cluster=instance.name)
    helmchart.save()

    instance.helmchart_id = helmchart.id
    post_save.disconnect(post_save_cluster, sender=Cluster, dispatch_uid='cluster_post_save_signal')
    instance.save()
    post_save.connect(post_save_cluster, sender=Cluster, dispatch_uid='cluster_post_save_signal')