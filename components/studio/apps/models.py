from django.db import models
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.conf import settings
from django.template import engines
from deployments.models import HelmResource
from models.models import Model
from projects.models import Project, Volume
from projects.helpers import get_minio_keys
from django.contrib.auth.models import User
from modules import keycloak_lib as keylib
# from .tasks import add_valid_redirect_uri, deploy_resource, delete_resource
import uuid
import flatten_json


class AppPermission(models.Model):
    name = models.CharField(max_length=512, default="permission_name")
    public = models.BooleanField(default=False)
    projects = models.ManyToManyField('projects.Project')
    users = models.ManyToManyField(User)
    def __str__(self):
        return str(self.name)

class AppCategories(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, default="", primary_key=True)
    def __str__(self):
        return str(self.name)

class Apps(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, blank=True, null=True)
    category = models.ForeignKey('AppCategories', related_name="apps", on_delete=models.CASCADE, null=True)
    settings = models.JSONField(blank=True, null=True)
    chart = models.CharField(max_length=512)
    description = models.TextField(blank=True, null=True, default="")
    table_field = models.TextField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class AppInstance(models.Model):
    # TODO: Name, project should be unique combination
    name = models.CharField(max_length=512, default="app_name")
    permission = models.OneToOneField('apps.AppPermission', on_delete=models.DO_NOTHING, null=True)
    app = models.ForeignKey('Apps', on_delete=models.CASCADE, related_name='appinstance')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='appinstance')
    app_dependencies = models.ManyToManyField('apps.AppInstance')
    model_dependencies = models.ManyToManyField('models.Model')
    # env_dependencies = models.ManyToManyField('projects.Environment')
    # flavor_dependencies = models.ManyToManyField('projects.Flavor')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_owner', null=True)
    url = models.CharField(max_length=512, null=True)
    info = models.TextField(blank=True, null=True)
    settings = models.TextField(blank=True, null=True)
    parameters = models.JSONField(blank=True, null=True)
    table_field = models.CharField(max_length=512, null=True)
    keycloak_client_id = models.CharField(max_length=512, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


@receiver(pre_delete, sender=AppInstance, dispatch_uid='appinstance_pre_delete_signal')
def pre_delete_appinstance(sender, instance, using, **kwargs):
    try:
        kc = keylib.keycloak_init()
        # TODO: Fix for multicluster setup
        URI =  'https://'+instance.parameters['release']+'.'+settings.DOMAIN
        
        # Clean up in Keycloak.
        print("Delete Keycloak objects.")
        print("Model: remove client redirect.")
        keylib.keycloak_remove_client_valid_redirect(kc, instance.project.slug, URI.strip('/')+'/*')
        print("Model: delete client.")
        print("client: {}".format(instance.parameters['gatekeeper']['client_id']))
        keylib.keycloak_delete_client(kc, instance.parameters['gatekeeper']['client_id']) 
        print("Model: get client scope.")
        scope_id = keylib.keycloak_get_client_scope_id(kc, instance.parameters['gatekeeper']['client_id']+'-scope')
        keylib.keycloak_delete_client_scope(kc, scope_id)
        
        # Uninstall resources
        # print("Uninstalling resources.")
        # delete_resource.delay(instance.parameters)
        
        instance.permission.delete()
    except Exception as err:
        print("Failed to delete AppInstance.")
        print(err)
