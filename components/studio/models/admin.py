from django.contrib import admin

from .models import Model, ModelLog, Metadata

admin.site.register(Model)
admin.site.register(ModelLog)
admin.site.register(Metadata)
