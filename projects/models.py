import base64
import random
import secrets
import string

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify
from guardian.shortcuts import assign_perm
from rest_framework.authtoken.models import Token


#@receiver(post_save, sender=settings.AUTH_USER_MODEL)
#def create_auth_token(sender, instance=None, created=False, **kwargs):
#    if created:
#        Token.objects.create(user=instance)


class BasicAuth(models.Model):
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    password = models.CharField(max_length=100, blank=True, default="")
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE, related_name='ba_project', null=True)
    username = models.CharField(max_length=100, blank=True, default="")


class Environment(models.Model):
    app = models.ForeignKey(settings.APPS_MODEL,
                            on_delete=models.CASCADE, null=True)
    appenv = models.ForeignKey(settings.APPINSTANCE_MODEL, related_name="envobj",
                               null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE, null=True)
    registry = models.ForeignKey(
        settings.APPINSTANCE_MODEL, related_name="environments", null=True, blank=True, on_delete=models.CASCADE)
    repository = models.CharField(max_length=100, blank=True, null=True)
    slug = models.CharField(max_length=100, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class Flavor(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    cpu_lim = models.TextField(blank=True, null=True, default="1000m")
    gpu_lim = models.TextField(blank=True, null=True, default="0")
    ephmem_lim = models.TextField(blank=True, null=True, default="200Mi")
    mem_lim = models.TextField(blank=True, null=True, default="3Gi")
    cpu_req = models.TextField(blank=True, null=True, default="200m")
    gpu_req = models.TextField(blank=True, null=True, default="0")
    ephmem_req = models.TextField(blank=True, null=True, default="200Mi")
    mem_req = models.TextField(blank=True, null=True, default="0.5Gi")
    name = models.CharField(max_length=512)
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class S3(models.Model):
    access_key = models.CharField(max_length=512)
    app = models.OneToOneField(
        settings.APPINSTANCE_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="s3obj")
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.CharField(max_length=512)
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE, related_name='s3_project')
    region = models.CharField(max_length=512, blank=True, default="")
    secret_key = models.CharField(max_length=512)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.project.slug)


class MLFlow(models.Model):
    app = models.OneToOneField(settings.APPINSTANCE_MODEL, on_delete=models.CASCADE,
                               null=True, blank=True, related_name="mlflowobj")
    basic_auth = models.ForeignKey(
        BasicAuth, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    mlflow_url = models.CharField(max_length=512)
    host = models.CharField(max_length=512, blank=True, default="")
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE, related_name='mlflow_project')
    s3 = models.ForeignKey(
        S3, on_delete=models.DO_NOTHING, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} ({})'.format(self.name, self.project.slug)


# it will become the default objects attribute for a Project model
class ProjectManager(models.Manager):

    def create_project(self, name, owner, description, repository):
        key = self.generate_passkey()
        letters = string.ascii_lowercase
        secret = self.generate_passkey(40)
        slug = slugify(name)
        slug_extension = ''.join(random.choice(letters) for i in range(3))
        slug = '{}-{}'.format(slugify(slug), slug_extension)

        project = self.create(name=name, owner=owner, slug=slug, project_key=key, project_secret=secret,
                              description=description, repository=repository,
                              repository_imported=False)

        assign_perm('can_view_project', owner, project)
        return project

    def generate_passkey(self, length=20):
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Encrypt the key
        password = password.encode('ascii')
        base64_bytes = base64.b64encode(password)
        password = base64_bytes.decode('ascii')

        return password



class Project(models.Model):
    authorized = models.ManyToManyField(get_user_model(), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    clone_url = models.CharField(max_length=512, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    mlflow = models.OneToOneField(
        MLFlow, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_mlflow')
    name = models.CharField(max_length=512)
    objects = ProjectManager()
    owner = models.ForeignKey(
        get_user_model(), on_delete=models.DO_NOTHING, related_name='owner')
    project_image = models.ImageField(
        upload_to='projects/images/', null=True, blank=True, default=None)
    s3storage = models.OneToOneField(
        S3, on_delete=models.SET_NULL, null=True, blank=True, related_name='project_s3')
    slug = models.CharField(max_length=512, unique=True)
    status = models.CharField(max_length=20, null=True,
                              blank=True, default="active")
    updated_at = models.DateTimeField(auto_now=True)

    # These fields should be removed.
    image = models.CharField(max_length=2048, blank=True, null=True)
    project_key = models.CharField(max_length=512)
    project_secret = models.CharField(max_length=512)
    # ----------------------
    # These fields should be removed.
    repository = models.CharField(max_length=512, null=True, blank=True)
    repository_imported = models.BooleanField(default=False)
    # ----------------------

    class Meta:
        permissions = [
            ('can_view_project', 'Can view project')
        ]

    def __str__(self):
        return "Name: {} ({})".format(self.name, self.status)


@receiver(pre_delete, sender=Project)
def on_project_delete(sender, instance, **kwargs):
    
    Model = apps.get_model(app_label=settings.MODELS_MODEL)
    print("ARCHIVING PROJECT MODELS")
    models = Model.objects.filter(project=instance)

    for model in models:
        model.status = 'AR'
        model.save()    

class ProjectLog(models.Model):
    MODULE_CHOICES = [
        ('DE', 'deployments'),
        ('LA', 'labs'),
        ('MO', 'models'),
        ('PR', 'projects'),
        ('RE', 'reports'),
        ('UN', 'undefined'),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=512)
    headline = models.CharField(max_length=256)
    module = models.CharField(
        max_length=2, choices=MODULE_CHOICES, default='UN')
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE)


class ProjectTemplate(models.Model):
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(
        upload_to='projecttemplates/images/', blank=True, null=True)
    name = models.CharField(max_length=512)
    revision = models.IntegerField(default=1)
    slug = models.CharField(max_length=512, default="")
    template = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ('slug', 'revision',)

    def __str__(self):
        return '{} ({})'.format(self.name, self.revision)


class ReleaseName(models.Model):
    app = models.ForeignKey(settings.APPINSTANCE_MODEL,
                            on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=512)
    status = models.CharField(max_length=10)
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return '{}-{}-{}'.format(self.name, self.project, self.app)
