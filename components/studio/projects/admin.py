from django.contrib import admin

from .models import Project, Environment


admin.site.register(Project)
admin.site.register(Environment)
