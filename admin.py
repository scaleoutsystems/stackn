from django.contrib import admin

from .models import Metadata, Model, ModelLog, ObjectType

admin.site.register(Model)
admin.site.register(ObjectType)
admin.site.register(ModelLog)
admin.site.register(Metadata)
