from apps.models import AppCategories, AppInstance, Apps, AppStatus
from django.contrib.auth.models import User
from models.models import Metadata, Model, ModelLog, ObjectType
from projects.models import (
    S3,
    Environment,
    Flavor,
    MLFlow,
    Project,
    ProjectTemplate,
    ReleaseName,
)
from rest_framework.serializers import ModelSerializer


class MLModelSerializer(ModelSerializer):
    class Meta:
        model = Model
        fields = (
            "id",
            "uid",
            "name",
            "description",
            "model_card",
            "resource",
            "url",
            "uploaded_at",
            "project",
            "status",
            "version",
            "object_type",
        )


class ObjectTypeSerializer(ModelSerializer):
    class Meta:
        model = ObjectType
        fields = ("id", "name", "slug")


class ModelLogSerializer(ModelSerializer):
    class Meta:
        model = ModelLog
        fields = (
            "id",
            "run_id",
            "trained_model",
            "project",
            "training_started_at",
            "execution_time",
            "code_version",
            "current_git_repo",
            "latest_git_commit",
            "system_details",
            "cpu_details",
            "training_status",
        )


class MetadataSerializer(ModelSerializer):
    class Meta:
        model = Metadata
        fields = (
            "id",
            "run_id",
            "trained_model",
            "project",
            "model_details",
            "parameters",
            "metrics",
        )


class S3serializer(ModelSerializer):
    class Meta:
        model = S3
        fields = ("name", "access_key", "secret_key", "host", "region")


class MLflowSerializer(ModelSerializer):
    s3 = S3serializer()

    class Meta:
        model = MLFlow
        fields = ("name", "mlflow_url", "s3")


class ProjectSerializer(ModelSerializer):
    s3storage = S3serializer()

    class Meta:
        model = Project

        fields = (
            "id",
            "name",
            "description",
            "slug",
            "owner",
            "authorized",
            "image",
            "s3storage",
            "updated_at",
            "created_at",
            "repository",
            "repository_imported",
        )


class AppCategorySerializer(ModelSerializer):
    class Meta:
        model = AppCategories
        fields = ("name",)


class AppSerializer(ModelSerializer):
    category = AppCategorySerializer()

    class Meta:
        model = Apps
        fields = ("id", "revision", "name", "category")


class AppStatusSerializer(ModelSerializer):
    class Meta:
        model = AppStatus
        fields = ("id", "status_type")


class AppInstanceSerializer(ModelSerializer):
    app = AppSerializer()
    status = AppStatusSerializer(many=True)

    class Meta:
        model = AppInstance
        fields = ("id", "name", "app", "table_field", "state", "status")


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class FlavorsSerializer(ModelSerializer):
    class Meta:
        model = Flavor
        fields = "__all__"


class EnvironmentSerializer(ModelSerializer):
    app = AppSerializer()

    class Meta:
        model = Environment
        fields = "__all__"


class ReleaseNameSerializer(ModelSerializer):
    app = AppInstanceSerializer()

    class Meta:
        model = ReleaseName
        fields = "__all__"


class ProjectTemplateSerializer(ModelSerializer):
    class Meta:
        model = ProjectTemplate
        fields = "__all__"
