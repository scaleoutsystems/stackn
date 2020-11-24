from django.db import models
from models.models import compare_version
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.utils.module_loading import import_string
from django.conf import settings
from functools import cmp_to_key

class ModelManager(models.Manager):

    def sorted_by_version(self, dataset_name, project_slug):
        datasets = super().get_queryset().filter(project_slug=project_slug,
                                               name=dataset_name)
        if datasets:
            datasets = sorted(datasets, key=cmp_to_key(compare_version))
            return datasets
        return []

    # Get latest version.
    def latest(self, model_name, project_slug):
        # Get all datasets in the project
        datasets = super().get_queryset().filter(project_slug=project_slug, name=model_name)
        if datasets:
            # Sort by version
            datasets = sorted(datasets, key=cmp_to_key(compare_version))
            for dataset in datasets:
                print('{}-{}'.format(dataset.name, dataset.version))
            return datasets[0]

        return []


class FileModel(models.Model):
    name = models.CharField(max_length=255)
    bucket = models.CharField(max_length=255, default="dataset")

class Dataset(models.Model):
    objects_version = ModelManager()
    objects = models.Manager()
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    release_type = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    bucket = models.CharField(max_length=255, default="dataset")
    project_slug = models.CharField(max_length=255, default="")
    files = models.ManyToManyField(FileModel, blank=True)
    created_by = models.CharField(max_length=255) # Username
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('name', 'version', 'project_slug')

class Datasheet(models.Model):
    objects_version = ModelManager()
    objects = models.Manager
    name = models.CharField(max_length=255)

@receiver(pre_save, sender=Dataset, dispatch_uid='dataset_pre_save_signal')
def pre_save_model(sender, instance, using, **kwargs):
    # Load version backend
    VERSION_CLASS = import_string(settings.VERSION_BACKEND)
    # Set version
    release_type = instance.release_type
    # If version is not already set, create new release
    if not instance.version:
        # Get latest release and bump:
        dataset = Dataset.objects_version.latest(instance.name, instance.project_slug)
        if not dataset:
            # This is the first release
            new_version = VERSION_CLASS()
        else:
            new_version = VERSION_CLASS(dataset.version)
        

        release_status, instance.version = new_version.release(release_type)
        print('New version: '+instance.version)
        if not release_status:
            raise Exception('Failed to create new release for model {}-{}, release type {}.'.format(instance.name, instance.version, release_type))

# @receiver(pre_delete, sender=Dataset, dispatch_uid='dataset_pre_delete_signal')
# def pre_delete_dataset(sender, instance, using, **kwargs):
#     files = instance.files
#     for f in files:
#         f.delete()