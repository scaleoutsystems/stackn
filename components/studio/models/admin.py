from django.contrib import admin

from .models import Model, ModelLog

admin.site.register(Model)
admin.site.register(ModelLog)
