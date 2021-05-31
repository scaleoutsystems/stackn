from django.conf.urls import include
from django.urls import path
import rest_framework.routers as drfrouters
from .views import ModelList, ModelLogList, MetadataList, ProjectList, MembersList, ObjectTypeList
from .views import AppInstanceList, FlavorsList, EnvironmentList, S3List, MLflowList, ResourceList
from .views import ReleaseNameList, AppList
from .public_views import get_studio_settings
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_nested import routers

app_name = 'api'

router_drf = drfrouters.DefaultRouter()

router = routers.SimpleRouter()

router.register(r'projects', ProjectList, basename='project')
router.register(r'apps', AppList, basename='apps')

models_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
models_router.register(r'models', ModelList, basename='model')
models_router.register(r'objecttype', ObjectTypeList, basename='objecttype')
models_router.register(r'members', MembersList, basename='members')
models_router.register(r'resources', ResourceList, basename='resources')
models_router.register(r'appinstances', AppInstanceList, basename='appinstances')
models_router.register(r'flavors', FlavorsList, basename='flavors')
models_router.register(r'environments', EnvironmentList, basename='environment')
models_router.register(r's3', S3List, basename='s3')
models_router.register(r'mlflow', MLflowList, basename='mlflow')
models_router.register(r'releasenames', ReleaseNameList, basename='releasenames')
models_router.register(r'modellogs', ModelLogList, basename='modellog')
models_router.register(r'metadata', MetadataList, basename='metadata')
models_router.register(r'apps', AppList, basename='apps')



urlpatterns = [
    path('', include(router_drf.urls)),
    path('', include(router.urls)),
    path('', include(models_router.urls)),
    path('api-token-auth', obtain_auth_token, name='api_token_auth'),
    path('settings', get_studio_settings)
]
