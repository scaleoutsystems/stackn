from django.contrib import admin

from .models import Apps, AppInstance, AppCategories, AppPermission, ResourceData, AppStatus


admin.site.register(Apps)
admin.site.register(AppInstance)
admin.site.register(AppCategories)
admin.site.register(AppPermission)
admin.site.register(ResourceData)
admin.site.register(AppStatus)