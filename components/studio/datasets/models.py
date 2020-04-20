from django.db import models


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    data = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey('projects.Project', on_delete=models.DO_NOTHING, related_name='dataset_owner')
