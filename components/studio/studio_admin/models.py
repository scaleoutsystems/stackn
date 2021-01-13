from django.db import models

class ActivityLog(models.Model):
    headline = models.CharField(max_length=256)
    description = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
