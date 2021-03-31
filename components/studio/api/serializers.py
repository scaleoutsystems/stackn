from rest_framework.serializers import ModelSerializer

from models.models import Model, ModelLog, Metadata, ObjectType
from projects.models import Project, S3
from django.contrib.auth.models import User

class MLModelSerializer(ModelSerializer):
    class Meta:
        model = Model
        fields = (
            'id', 'uid', 'name', 'description', 'resource', 'url', 'uploaded_at', 'project', 'status', 'version', 'object_type')

class ObjectTypeSerializer(ModelSerializer):
    class Meta:
        model = ObjectType
        fields = ('id', 'name', 'slug')

class ModelLogSerializer(ModelSerializer):
    class Meta:
        model = ModelLog
        fields = (
            'id', 'run_id', 'trained_model', 'project', 'training_started_at', 'execution_time', 'code_version', 
            'current_git_repo', 'latest_git_commit', 'system_details', 'cpu_details', 'training_status')


class MetadataSerializer(ModelSerializer):
    class Meta:
        model = Metadata
        fields = (
            'id', 'run_id', 'trained_model', 'project', 'model_details', 'parameters', 'metrics')


class S3serializer(ModelSerializer):
    class Meta:
        model = S3
        fields = ('access_key', 'secret_key', 'host', 'region')

class ProjectSerializer(ModelSerializer):
    s3storage = S3serializer()
    class Meta:
        model = Project
        
        fields = (
            'id', 'name', 'description', 'slug', 'owner', 'authorized', 'image', 's3storage', 'updated_at',
            'created_at', 'repository', 'repository_imported')

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

