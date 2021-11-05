
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth', views.auth),
    path('account/', include('django.contrib.auth.urls')),
    #path('oidc/', include('mozilla_django_oidc.urls')),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('', include('portal.urls', namespace='portal')),
    path('', include('models.urls', namespace='models')),
    path('', include('deployments.urls', namespace="deployments")),
    #path('workflows/', include('workflows.urls', namespace='workflows')),
    path('api/', include('api.urls', namespace='api')),
    path('', include('projects.urls', namespace='projects')),
    #path('<user>/<project>/datasets/', include('datasets.urls', namespace='datasets')),
    #path('<user>/<project>/files/', include('files.urls', namespace='files')),
    #path('<user>/<project>/reports/', include('reports.urls', namespace='reports')),
    path('<user>/<project>/monitor/', include('monitor.urls', namespace='monitor')),
    path('<user>/<project>/apps/', include('apps.urls', namespace='apps')),
    #path('studio/admin/', include('studio_admin.urls', namespace='studio_admin')),
    #path('django_plotly_dash/', include('django_plotly_dash.urls'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Since this is a production feature, it will only work if DEBUG is set to False
handler404 = 'studio.views.handle_page_not_found'

