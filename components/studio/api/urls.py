from django.conf.urls import include
from django.urls import path
from rest_framework import routers
from .views import ModelViewSet, ReportViewSet, ReportGeneratorViewSet, ProjectViewSet, GetProjectInfo
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'models', ModelViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'generators', ReportGeneratorViewSet)
router.register(r'projects', ProjectViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('user/<str:project_owner_name>/project/<str:project_name>', GetProjectInfo.as_view()),
    path('api-token-auth', obtain_auth_token, name='api_token_auth'),
]
