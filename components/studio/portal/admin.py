from django.contrib import admin

from .models import PublicModelObject, PublishedModel

admin.site.register(PublishedModel)
admin.site.register(PublicModelObject)
