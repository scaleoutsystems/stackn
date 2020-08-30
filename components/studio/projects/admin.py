from django.contrib import admin

from .models import Project, Environment, Flavor, ProjectLog


admin.site.register(Project)
admin.site.register(Environment)
admin.site.register(Flavor)
admin.site.register(ProjectLog)
