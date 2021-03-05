from django.conf.urls import include
from django.urls import path
import rest_framework.routers as drfrouters
from .views import ModelList, ModelLogList, MetadataList, ReportList, ReportGeneratorList, ProjectList, DeploymentInstanceList, \
    DeploymentDefinitionList, LabsList, MembersList, DatasetList, VolumeList, JobsList
from .public_views import get_studio_settings
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_nested import routers

app_name = 'api'

router_drf = drfrouters.DefaultRouter()

router = routers.SimpleRouter()

router.register(r'reports', ReportList, basename='report')
router.register(r'generators', ReportGeneratorList, basename='report_generator')
router.register(r'projects', ProjectList, basename='project')

models_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
models_router.register(r'models', ModelList, basename='model')
models_router.register(r'labs', LabsList, basename='lab')
models_router.register(r'members', MembersList, basename='members')
models_router.register(r'dataset', DatasetList, basename='dataset')
models_router.register(r'volumes', VolumeList, basename='volumes')
models_router.register(r'modellogs', ModelLogList, basename='modellog')
models_router.register(r'metadata', MetadataList, basename='metadata')
models_router.register(r'jobs', JobsList, basename='jobs')

router.register(r'deploymentInstances', DeploymentInstanceList, basename='deploymentInstance')
router.register(r'deploymentDefinitions', DeploymentDefinitionList, basename='deploymentDefinition')

urlpatterns = [
    path('', include(router_drf.urls)),
    path('', include(router.urls)),
    path('', include(models_router.urls)),
    path('api-token-auth', obtain_auth_token, name='api_token_auth'),
    path('settings', get_studio_settings)
]
