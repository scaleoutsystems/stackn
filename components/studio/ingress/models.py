from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
import yaml


class Page(models.Model):
    name = models.CharField(max_length=255)

    page = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)