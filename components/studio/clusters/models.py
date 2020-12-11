from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils.text import slugify

import modules.keycloak_lib as keylib

class Cluster(models.Model):
    name = models.CharField(max_length=512, unique=True)
    base_url = models.CharField(max_length=512)
    config = models.TextField()
    namespace = models.CharField(max_length=512)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "{}".format(self.name)