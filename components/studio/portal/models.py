import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.template import engines
from django.utils.text import slugify

from models.models import Model


class PublicModelObject(models.Model):
    model = models.OneToOneField('models.Model', on_delete=models.CASCADE)
    obj = models.FileField(upload_to='models/objects/')
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)


class PublishedModel(models.Model):
    name = models.CharField(max_length=512)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    model_obj = models.ManyToManyField(PublicModelObject)
    img = models.ImageField(upload_to='models/image',
                            null=True, blank=True, default=None)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
