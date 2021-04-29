from django.contrib import admin

from .models import Model, ModelLog, Metadata, ObjectType

admin.site.register(Model)
admin.site.register(ObjectType)
admin.site.register(ModelLog)
admin.site.register(Metadata)
