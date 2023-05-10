from django.contrib import admin

from .models import AppCategories, AppInstance, Apps, AppStatus, ResourceData


class AppsAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user_can_create",
        "user_can_edit",
        "user_can_delete",
        "slug",
    )
    list_filter = ("user_can_create",)


admin.site.register(Apps, AppsAdmin)


class AppInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "display_owner",
        "display_project",
        "state",
        "access",
    )

    list_filter = ["owner", "project", "state"]

    def display_owner(self, obj):
        return obj.owner.username

    def display_project(self, obj):
        return obj.project.name


admin.site.register(AppInstance, AppInstanceAdmin)
admin.site.register(AppCategories)
admin.site.register(ResourceData)
admin.site.register(AppStatus)
