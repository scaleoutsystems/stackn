from rest_framework.serializers import ModelSerializer

from models.models import Model
from reports.models import Report, ReportGenerator
from projects.models import Project
from deployments.models import DeploymentInstance, DeploymentDefinition
from labs.models import Session
from django.contrib.auth.models import User
class MLModelSerializer(ModelSerializer):
    class Meta:
        model = Model
        fields = (
            'id', 'uid', 'name', 'description', 'resource', 'url', 'uploaded_at', 'project', 'status', 'version')

class DeploymentDefinitionSerializer(ModelSerializer):
    class Meta:
        model = DeploymentDefinition
        fields = (
            'id', 'project','name', 'bucket','filename','path_predict')


class DeploymentInstanceSerializer(ModelSerializer):
    class Meta:
        model = DeploymentInstance
        fields = ('id','deployment', 'model', 'access', 'endpoint', 'created_at')


class ReportSerializer(ModelSerializer):
    class Meta:
        model = Report
        fields = (
            'id', 'model', 'description', 'created_at', 'report', 'job_id', 'generator', 'status')


class ReportGeneratorSerializer(ModelSerializer):
    class Meta:
        model = ReportGenerator
        fields = (
            'id', 'project', 'description', 'generator', 'visualiser', 'created_at')


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id', 'name', 'description', 'slug', 'owner', 'authorized', 'image', 'project_key', 'project_secret', 'updated_at',
            'created_at', 'repository', 'repository_imported')


class LabSessionSerializer(ModelSerializer):
    class Meta:
        model = Session
        fields = (
            'id', 'name', 'slug', 'project', 'lab_session_owner', 'flavor_slug', 'environment_slug', 'status',
            'created_at', 'updated_at')

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']