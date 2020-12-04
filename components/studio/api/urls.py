from django.conf.urls import include
from django.urls import path
import rest_framework.routers as drfrouters
from .views import ModelList, ModelLogList, MetadataList, ReportList, ReportGeneratorList, ProjectList, DeploymentInstanceList, \
    DeploymentDefinitionList, LabsList, MembersList, DatasetList, VolumeList, JobsList

from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_nested import routers

app_name = 'api'

router_drf = drfrouters.DefaultRouter()

router = routers.SimpleRouter()

router.register(r'reports', ReportList, base_name='report')
router.register(r'generators', ReportGeneratorList, base_name='report_generator')
router.register(r'projects', ProjectList, base_name='project')

models_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
models_router.register(r'models', ModelList, base_name='model')
models_router.register(r'labs', LabsList, base_name='lab')
models_router.register(r'members', MembersList, base_name='members')
models_router.register(r'dataset', DatasetList, base_name='dataset')
models_router.register(r'volumes', VolumeList, base_name='volumes')
models_router.register(r'modellogs', ModelLogList, base_name='modellog')
models_router.register(r'metadata', MetadataList, base_name='metadata')
models_router.register(r'jobs', JobsList, base_name='jobs')


router.register(r'deploymentInstances', DeploymentInstanceList, base_name='deploymentInstance')
router.register(r'deploymentDefinitions', DeploymentDefinitionList, base_name='deploymentDefinition')

urlpatterns = [
    path('', include(router_drf.urls)),
    path('', include(router.urls)),
    path('', include(models_router.urls)),
    path('api-token-auth', obtain_auth_token, name='api_token_auth'),
]
