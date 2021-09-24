from django.db import models
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.conf import settings
from django.template import engines
from models.models import Model
from django.contrib.auth.models import User
from modules import keycloak_lib as keylib
import uuid
import flatten_json
from datetime import datetime, timedelta


class RequestAccount(models.Model):
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    org = models.CharField(max_length=512)
    email = models.EmailField(max_length=254)
    use = models.TextField()
    deployed = models.TextField()
    resources = models.TextField()
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta: app_label = 'studio'