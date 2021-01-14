from django.db import models
from django.contrib.auth.models import User

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=null)
    headline = models.CharField(max_length=256)
    description = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
