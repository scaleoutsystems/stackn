from django.contrib import admin

from .models import DeploymentDefinition, DeploymentInstance

admin.site.register(DeploymentDefinition)
admin.site.register(DeploymentInstance)
