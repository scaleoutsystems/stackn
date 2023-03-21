from django.contrib import admin

from .models import Metadata, Model, ModelLog, ObjectType


class ModelAdmin(admin.ModelAdmin):
    empty_value_display = "-"
    list_display = ("name", "version", "project_name", "object_type_name")

    def project_name(self, obj):
        return obj.project.name

    def object_type_name(self, obj):
        return obj.object_type.name


admin.site.register(Model, ModelAdmin)
admin.site.register(ObjectType)
admin.site.register(ModelLog)
admin.site.register(Metadata)
