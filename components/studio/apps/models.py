from django.db import models
from models.models import Model
from projects.models import Project
from django.contrib.auth.models import User
from tagulous.models import TagField


class AppPermission(models.Model):
    appinstance = models.OneToOneField('apps.AppInstance', on_delete=models.CASCADE, null=True, related_name="permission")
    name = models.CharField(max_length=512, default="permission_name")
    projects = models.ManyToManyField('projects.Project')
    public = models.BooleanField(default=False)
    users = models.ManyToManyField(User)
    
    def __str__(self):
        return str(self.name)


class AppCategories(models.Model):
    name = models.CharField(max_length=512)
    priority = models.IntegerField(default=100)
    slug = models.CharField(max_length=512, default="", primary_key=True)
    
    def __str__(self):
        return str(self.name)


class Apps(models.Model):
    access = models.CharField(max_length=20, blank=True, null=True, default="public")
    category = models.ForeignKey('AppCategories', related_name="apps", on_delete=models.CASCADE, null=True)
    chart = models.CharField(max_length=512)
    chart_archive = models.FileField(upload_to='apps/', null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True, default="")
    logo = models.CharField(max_length=512, default="dist/logo.png")
    logo_file = models.FileField(upload_to='apps/logos/', null=True, blank=True)
    name = models.CharField(max_length=512)
    priority = models.IntegerField(default=100)
    projects = models.ManyToManyField('projects.Project')
    revision = models.IntegerField(default=1)
    settings = models.JSONField(blank=True, null=True)
    slug = models.CharField(max_length=512, blank=True, null=True)
    table_field = models.JSONField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('slug', 'revision',)

    def __str__(self):
        return str(self.name)+'({})'.format(self.revision)


class AppInstance(models.Model):
    access = models.CharField(max_length=20, default="private", null=True, blank=True)
    app = models.ForeignKey('Apps', on_delete=models.CASCADE, related_name='appinstance')
    app_dependencies = models.ManyToManyField('apps.AppInstance', blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    info = models.JSONField(blank=True, null=True)
    model_dependencies = models.ManyToManyField('models.Model', blank=True)
    name = models.CharField(max_length=512, default="app_name")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_owner', null=True)
    parameters = models.JSONField(blank=True, null=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='appinstance')
    state = models.CharField(max_length=50, null=True, blank=True)
    table_field = models.JSONField(blank=True, null=True)
    tags = TagField()
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)+' ({})-{}-{}-{}'.format(self.state, self.owner, self.app.name, self.project)


class AppStatus(models.Model):
    appinstance = models.ForeignKey('AppInstance', on_delete=models.CASCADE, related_name="status")
    info = models.JSONField(blank=True, null=True)
    status_type = models.CharField(max_length=15, default="app_name")
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'time'

    def __str__(self):
        return str(self.appinstance.name)+"({})".format(self.time)
    

class ResourceData(models.Model):
    appinstance = models.ForeignKey('AppInstance', on_delete=models.CASCADE, related_name="resourcedata")
    cpu = models.IntegerField()
    gpu = models.IntegerField()
    mem = models.IntegerField()
    time = models.IntegerField()
