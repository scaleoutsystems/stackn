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
from . import views


urlpatterns = [
    path('', include('common.urls', namespace='common')),
    #path('', include('deployments.urls', namespace="deployments")),
    path('', include('models.urls', namespace='models')),
    path('', include('portal.urls', namespace='portal')),
    path('', include('projects.urls', namespace='projects')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    #path('oidc/', include('mozilla_django_oidc.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('<user>/<project>/monitor/', include('monitor.urls', namespace='monitor')),
    path('<user>/<project>/apps/', include('apps.urls', namespace='apps')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Since this is a production feature, it will only work if DEBUG is set to False
handler404 = 'studio.views.handle_page_not_found'
