from django.contrib import admin

from .models import Apps, AppInstance


admin.site.register(Apps)
admin.site.register(AppInstance)