from django.conf.urls import include
from django.urls import path
from rest_framework import routers
from .views import ModelList, ReportList, ReportGeneratorList, ProjectList
from rest_framework.authtoken.views import obtain_auth_token

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'models', ModelList, basename='model')
router.register(r'reports', ReportList, basename='report')
router.register(r'generators', ReportGeneratorList, basename='report_generator')
router.register(r'projects', ProjectList, basename='project')

urlpatterns = [
    path('', include(router.urls)),
    path('api-token-auth', obtain_auth_token, name='api_token_auth'),
]
