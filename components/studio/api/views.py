from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated

from .serializers import Model, MLModelSerializer, Report, ReportSerializer, \
    ReportGenerator, ReportGeneratorSerializer, Project, ProjectSerializer


class ModelViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)

    queryset = Model.objects.all()
    serializer_class = MLModelSerializer


class ReportViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)

    queryset = Report.objects.all()
    serializer_class = ReportSerializer


class ReportGeneratorViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)

    queryset = ReportGenerator.objects.all()
    serializer_class = ReportGeneratorSerializer


class ProjectViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class GetProjectInfo(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_owner_name, project_name):
        project = Project.objects \
            .filter(owner__username=project_owner_name) \
            .filter(name=project_name) \
            .first()

        result = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner": project_owner_name,
            "project_key": project.project_key,
            "project_secret": project.project_secret,
            "updated_at": project.updated_at,
            "created_at": project.created_at
        }

        return Response(result)
