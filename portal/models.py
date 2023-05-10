import random

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver


class PublicModelObject(models.Model):
    model = models.OneToOneField(
        settings.MODELS_MODEL, on_delete=models.CASCADE
    )
    obj = models.FileField(upload_to="models/objects/")
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)


class PublishedModel(models.Model):
    name = models.CharField(max_length=512)
    project = models.ForeignKey(
        settings.PROJECTS_MODEL, on_delete=models.CASCADE
    )
    model_obj = models.ManyToManyField(PublicModelObject)
    pattern = models.CharField(max_length=255, default="")
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)


@receiver(pre_save, sender=PublishedModel)
def on_project_save(sender, instance, **kwargs):
    if instance.pattern == "":
        published_models = PublishedModel.objects.filter(
            project=instance.project
        )

        patterns = published_models.values_list("pattern", flat=True)

        arr = []

        for i in range(1, 31):
            pattern = f"pattern-{i}"

            if pattern not in patterns:
                arr.append(pattern)

        pattern = ""

        if len(arr) > 0:
            rand_index = random.randint(0, len(arr) - 1)

            pattern = arr[rand_index]

        else:
            randint = random.randint(1, 30)
            pattern = f"pattern-{randint}"

        instance.pattern = pattern
