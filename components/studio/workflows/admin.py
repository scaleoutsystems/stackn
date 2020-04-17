from django.contrib import admin

from .models import WorkflowDefinition, WorkflowInstance

admin.site.register(WorkflowDefinition)
admin.site.register(WorkflowInstance)
