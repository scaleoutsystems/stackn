from rest_framework.serializers import ModelSerializer

from models.models import Model
from reports.models import Report, ReportGenerator
from projects.models import Project


class MLModelSerializer(ModelSerializer):
    class Meta:
        model = Model
        fields = (
            'id', 'uid', 'name', 'description', 'url', 'project', 'tag')


class ReportSerializer(ModelSerializer):
    class Meta:
        model = Report
        fields = (
            'model', 'description', 'created_at', 'report', 'generator')


class ReportGeneratorSerializer(ModelSerializer):
    class Meta:
        model = ReportGenerator
        fields = (
            'project', 'description', 'generator', 'visualiser', 'created_at')


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id', 'name', 'description', 'slug', 'owner', 'project_key', 'project_secret', 'updated_at', 'created_at')
