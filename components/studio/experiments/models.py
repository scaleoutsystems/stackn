from django.db import models
import uuid


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    command = models.CharField(max_length=1024)
    environment = models.ForeignKey('projects.Environment', on_delete=models.CASCADE, related_name='job_environment')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='job_project')
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)
