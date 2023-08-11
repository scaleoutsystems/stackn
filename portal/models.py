from django.conf import settings
from django.db import models


class PublicModelObject(models.Model):
    model = models.OneToOneField(settings.MODELS_MODEL, on_delete=models.CASCADE)
    obj = models.FileField(upload_to="models/objects/")
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)


class PublishedModel(models.Model):
    name = models.CharField(max_length=512)
    project = models.ForeignKey(settings.PROJECTS_MODEL, on_delete=models.CASCADE)
    model_obj = models.ManyToManyField(PublicModelObject)
    img = models.ImageField(upload_to="models/image", null=True, blank=True, default=None)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
