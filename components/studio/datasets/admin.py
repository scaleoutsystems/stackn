from django.contrib import admin

from .models import Dataset, FileModel

admin.site.register(Dataset)
admin.site.register(FileModel)