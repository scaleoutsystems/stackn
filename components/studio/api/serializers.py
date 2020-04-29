from rest_framework.serializers import ModelSerializer

from models.models import Model
from reports.models import Report, ReportGenerator
from projects.models import Project
from deployments.models import DeploymentInstance, DeploymentDefinition


class MLModelSerializer(ModelSerializer):
    class Meta:
        model = Model
        fields = (
            'id', 'uid', 'name', 'description', 'resource', 'url', 'uploaded_at', 'project', 'status', 'tag')

class DeploymentDefinitionSerializer(ModelSerializer):
    class Meta:
        model = DeploymentDefinition
        fields = (
            'id', 'project','name', 'definition', 'bucket','filename','path_predict')


class DeploymentInstanceSerializer(ModelSerializer):
    class Meta:
        model = DeploymentInstance
        fields = (
            'deployment', 'model', 'name', 'access', 'endpoint', 'version')


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
            'id', 'name', 'description', 'slug', 'owner', 'image', 'project_key', 'project_secret', 'updated_at',
            'created_at', 'repository', 'repository_imported', 'environment')
