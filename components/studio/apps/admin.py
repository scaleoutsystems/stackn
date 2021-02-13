from django.contrib import admin

from .models import Apps, AppInstance, AppCategories


admin.site.register(Apps)
admin.site.register(AppInstance)
admin.site.register(AppCategories)