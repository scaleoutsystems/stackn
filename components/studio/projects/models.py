import base64

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.conf import settings
import string
import random

from deployments.models import HelmResource

class Volume(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, blank=True, null=True)
    size = models.CharField(max_length=512)
    project_slug = models.CharField(max_length=512)
    created_by = models.CharField(max_length=512)
    helmchart = models.OneToOneField('deployments.HelmResource', on_delete=models.CASCADE)
    settings = models.TextField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)

@receiver(pre_save, sender=Volume, dispatch_uid='volume_pre_save_signal')
def pre_save_volume(sender, instance, using, **kwargs):

    # TODO: Fix this for multicluster setup (deploy to cluster namespace, not Studio namespace)
    NAMESPACE = settings.NAMESPACE

    instance.slug = slugify(instance.name+'-'+instance.project_slug)
    user = instance.created_by
    parameters = {'release': instance.slug,
                  'chart': 'volume',
                  'name': instance.slug,
                  'namespace': NAMESPACE,
                  'accessModes': 'ReadWriteMany',
                  'storageClass': settings.STORAGECLASS,
                  'size': instance.size}
    helmchart = HelmResource(name=instance.slug,
                             namespace='Default',
                             chart='volume',
                             params=parameters,
                             username=user)
    helmchart.save()
    instance.helmchart = helmchart
    l = ProjectLog(project=Project.objects.get(slug=instance.project_slug), module='PR', headline='Volume',
                               description='A new volume {name} has been created'.format(name=instance.name))
    l.save()
class Flavor(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512)

    cpu = models.TextField(blank=True, null=True)
    mem = models.TextField(blank=True, null=True)
    gpu = models.TextField(blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class Environment(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, blank=True, null=True)
    image = models.CharField(max_length=512)
    dockerfile = models.TextField(default='FROM jupyter/base-notebook')
    startup = models.TextField(null=True, blank=True)
    teardown = models.TextField(null=True, blank=True)

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


class Project(models.Model):
    objects = ProjectManager()

    name = models.CharField(max_length=512, unique=True)
    description = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=512, unique=True)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='owner')
    authorized = models.ManyToManyField(User, blank=True)
    image = models.CharField(max_length=2048, blank=True, null=True)

    project_key = models.CharField(max_length=512)
    project_secret = models.CharField(max_length=512)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    repository = models.CharField(max_length=512, null=True, blank=True)
    repository_imported = models.BooleanField(default=False)

    def __str__(self):
        return "Name: {} Description: {}".format(self.name, self.description)

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

