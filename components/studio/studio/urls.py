"""studio URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('', include('models.urls', namespace='models')),
    path('', include('deployments.urls', namespace="deployments")),
    path('workflows/', include('workflows.urls', namespace='workflows')),
    path('api/', include('api.urls', namespace='api')),
    path('', include('projects.urls', namespace='projects')),
    path('<user>/<project>/labs/', include('labs.urls', namespace='labs')),
    path('<user>/<project>/datasets/', include('datasets.urls', namespace='datasets')),
    path('<user>/<project>/files/', include('files.urls', namespace='files')),
    path('<user>/<project>/reports/', include('reports.urls', namespace='reports')),
    path('<user>/<project>/experiments/', include('experiments.urls', namespace='experiments')),
    path('<user>/<project>/monitor/', include('monitor.urls', namespace='monitor')),
    path('studio/admin/', include('studio_admin.urls', namespace='studio_admin'))

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


import os

try:
    apps = [os.environ.get("APPS").split(" ")]
    for app in apps:
        urlpatterns += [path('', include('{}.urls'.format(app), namespace='{}'.format(app))),]
except Exception as e:
    pass
