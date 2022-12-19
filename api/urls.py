import rest_framework.routers as drfrouters
from django.conf.urls import include
from django.urls import path
from rest_framework_nested import routers

from .public_views import get_studio_settings
from .views import (
    AppInstanceList,
    AppList,
    CustomAuthToken,
    EnvironmentList,
    FlavorsList,
    MembersList,
    MetadataList,
    MLflowList,
    ModelList,
    ModelLogList,
    ObjectTypeList,
    ProjectList,
    ProjectTemplateList,
    ReleaseNameList,
    ResourceList,
    S3List,
)

app_name = "api"

router_drf = drfrouters.DefaultRouter()
router = routers.SimpleRouter()
router.register(r"projects", ProjectList, basename="project")
router.register(r"apps", AppList, basename="apps")
router.register(
    r"projecttemplates", ProjectTemplateList, basename="projecttemplates"
)

models_router = routers.NestedSimpleRouter(
    router, r"projects", lookup="project"
)
models_router.register(r"models", ModelList, basename="model")
models_router.register(r"objecttype", ObjectTypeList, basename="objecttype")
models_router.register(r"members", MembersList, basename="members")
models_router.register(r"resources", ResourceList, basename="resources")
models_router.register(
    r"appinstances", AppInstanceList, basename="appinstances"
)
models_router.register(r"flavors", FlavorsList, basename="flavors")
models_router.register(
    r"environments", EnvironmentList, basename="environment"
)
models_router.register(r"s3", S3List, basename="s3")
models_router.register(r"mlflow", MLflowList, basename="mlflow")
models_router.register(
    r"releasenames", ReleaseNameList, basename="releasenames"
)
models_router.register(r"modellogs", ModelLogList, basename="modellog")
models_router.register(r"metadata", MetadataList, basename="metadata")
models_router.register(r"apps", AppList, basename="apps")

urlpatterns = [
    path("", include(router_drf.urls)),
    path("", include(router.urls)),
    path("", include(models_router.urls)),
    path("token-auth/", CustomAuthToken.as_view(), name="api_token_auth"),
    path("settings/", get_studio_settings),
]
