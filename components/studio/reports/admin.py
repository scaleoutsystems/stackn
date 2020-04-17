from django.contrib import admin

from .models import Report, ReportGenerator

admin.site.register(Report)
admin.site.register(ReportGenerator)
