import base64

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.conf import settings
import string
import random
import uuid
from django_cryptography.fields import encrypt

class ReleaseName(models.Model):
    name = models.CharField(max_length=512)
    status = models.CharField(max_length=10)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True)
    app = models.ForeignKey('apps.AppInstance', on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return '{}-{}-{}'.format(self.name, self.project, self.app)

class Flavor(models.Model):
    name = models.CharField(max_length=512)

    cpu_req = models.TextField(blank=True, null=True, default="200m")
    mem_req = models.TextField(blank=True, null=True, default="0.5Gi")
    gpu_req = models.TextField(blank=True, null=True, default="0")
    ephmem_req = models.TextField(blank=True, null=True, default="200Mi")

    cpu_lim = models.TextField(blank=True, null=True, default="1000m")
    mem_lim = models.TextField(blank=True, null=True, default="3Gi")
    gpu_lim = models.TextField(blank=True, null=True, default="0")
    ephmem_lim = models.TextField(blank=True, null=True, default="200Mi")


    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True)
    # app = models.ForeignKey('apps.Apps', on_delete=models.CASCADE)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class Environment(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, null=True)
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True)

    repository = models.CharField(max_length=100, blank=True, null=True)
    image = models.CharField(max_length=100)

    registry = models.ForeignKey('apps.AppInstance', related_name="environments", null=True, blank=True, on_delete=models.CASCADE)
    appenv = models.ForeignKey('apps.AppInstance', related_name="envobj", null=True, blank=True, on_delete=models.CASCADE)
    app = models.ForeignKey('apps.Apps', on_delete=models.CASCADE, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class ProjectManager(models.Manager):
    def generate_passkey(self, length=20):
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Encrypt the key
        password = password.encode('ascii')
        base64_bytes = base64.b64encode(password)
        password = base64_bytes.decode('ascii')

        return password

    def create_project(self, name, owner, description, repository):
        letters = string.ascii_lowercase
        slug = slugify(name)
        slug_extension = ''.join(random.choice(letters) for i in range(3))

        slug = '{}-{}'.format(slugify(slug), slug_extension)
        key = self.generate_passkey()
        secret = self.generate_passkey(40)

        project = self.create(name=name, owner=owner, slug=slug, project_key=key, project_secret=secret,
                              description=description, repository=repository,
                              repository_imported=False)

        return project

class S3(models.Model):
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='s3_project')
    host = models.CharField(max_length=512)
    access_key = models.CharField(max_length=512)
    secret_key = models.CharField(max_length=512)
    region = models.CharField(max_length=512, blank=True, default="")
    app = models.OneToOneField('apps.AppInstance', on_delete=models.CASCADE, null=True, blank=True, related_name="s3obj")
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return '{} ({})'.format(self.name, self.project.slug)

class BasicAuth(models.Model):
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='ba_project', null=True)
    username = models.CharField(max_length=100, blank=True, default="")
    password = models.CharField(max_length=100, blank=True, default="")

class MLFlow(models.Model):
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='mlflow_project')
    mlflow_url = models.CharField(max_length=512)
    s3 = models.ForeignKey(S3, on_delete=models.DO_NOTHING, blank=True, null=True)
    basic_auth = models.ForeignKey(BasicAuth, on_delete=models.DO_NOTHING, null=True, blank=True)
    app = models.OneToOneField('apps.AppInstance', on_delete=models.CASCADE, null=True, blank=True, related_name="mlflowobj")
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return '{} ({})'.format(self.name, self.project.slug)

class ProjectTemplate(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, default="")
    revision = models.IntegerField(default=1)
    description = models.TextField(null=True, blank=True)
    template = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='projecttemplates/images/', null=True, blank=True, default=None)
    
    class Meta:
        unique_together = ('slug', 'revision',)
    
    def __str__(self):
        return '{} ({})'.format(self.name, self.revision)

class Project(models.Model):
    objects = ProjectManager()

    name = models.CharField(max_length=512)
    description = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=512, unique=True)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='owner')
    authorized = models.ManyToManyField(User, blank=True)

    s3storage = models.OneToOneField(S3, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='project_s3')
    mlflow = models.OneToOneField(MLFlow, on_delete=models.DO_NOTHING, null=True, blank=True, related_name='project_mlflow')

    status = models.CharField(max_length=20, null=True, blank=True, default="active")


    project_image = models.ImageField(upload_to='projects/images/', null=True, blank=True, default=None)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)



    # These fields should be removed.
    image = models.CharField(max_length=2048, blank=True, null=True)
    project_key = models.CharField(max_length=512)
    project_secret = models.CharField(max_length=512)
    # ----------------------
    # These fields should be removed.
    repository = models.CharField(max_length=512, null=True, blank=True)
    repository_imported = models.BooleanField(default=False)
    # ----------------------

    def __str__(self):
        return "Name: {} ({})".format(self.name, self.status)

    clone_url = models.CharField(max_length=512, null=True, blank=True)


class ProjectLog(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    MODULE_CHOICES = [
        ('DE', 'deployments'),
        ('LA', 'labs'),
        ('MO', 'models'),
        ('PR', 'projects'),
        ('RE', 'reports'),
        ('UN', 'undefined'),
    ]
    module = models.CharField(max_length=2, choices=MODULE_CHOICES, default='UN')

    headline = models.CharField(max_length=256)
    description = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)

