from django.db import models
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.conf import settings
from django.template import engines
from models.models import Model
from projects.models import Project
from projects.helpers import get_minio_keys
from django.contrib.auth.models import User
from modules import keycloak_lib as keylib
import uuid
import flatten_json
from datetime import datetime, timedelta


class AppPermission(models.Model):
    name = models.CharField(max_length=512, default="permission_name")
    public = models.BooleanField(default=False)
    projects = models.ManyToManyField('projects.Project')
    users = models.ManyToManyField(User)
    appinstance = models.OneToOneField('apps.AppInstance', on_delete=models.CASCADE, null=True, related_name="permission")
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
    table_field = models.JSONField(blank=True, null=True)
    logo = models.CharField(max_length=512, default="dist/applogos/stackn_logo_square.png")
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return str(self.name)


class AppInstance(models.Model):
    # TODO: Name, project should be unique combination
    name = models.CharField(max_length=512, default="app_name")
    app = models.ForeignKey('Apps', on_delete=models.CASCADE, related_name='appinstance')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='appinstance')
    app_dependencies = models.ManyToManyField('apps.AppInstance')
    model_dependencies = models.ManyToManyField('models.Model')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_owner', null=True)
    # url = models.CharField(max_length=512, null=True)
    info = models.JSONField(blank=True, null=True)
    parameters = models.JSONField(blank=True, null=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    table_field = models.JSONField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
    deleted_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.name)+' ({})-{}-{}'.format(self.state, self.owner, self.app.name)

class AppStatus(models.Model):
    appinstance = models.ForeignKey('AppInstance', on_delete=models.CASCADE, related_name="status")
    status_type = models.CharField(max_length=15, default="app_name")
    time = models.DateTimeField(auto_now_add=True)
    info = models.JSONField(blank=True, null=True)

    class Meta:
        get_latest_by = 'time'

    def __str__(self):
        return str(self.appinstance.name)+"({})".format(self.time)
    


class ResourceData(models.Model):
    appinstance = models.ForeignKey('AppInstance', on_delete=models.CASCADE, related_name="resourcedata")
    cpu = models.IntegerField()
    mem = models.IntegerField()
    gpu = models.IntegerField()
    time = models.IntegerField()