from django.contrib import admin

from .models import AppCategories, AppInstance, Apps, AppStatus, ResourceData


class AppsAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "user_can_create")
    list_filter = ("user_can_create",)


admin.site.register(Apps, AppsAdmin)
admin.site.register(AppInstance)
admin.site.register(AppCategories)
admin.site.register(ResourceData)
admin.site.register(AppStatus)
