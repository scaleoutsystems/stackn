from rest_framework.permissions import BasePermission
from django.http import QueryDict
from .serializers import Model, MLModelSerializer, Report, ReportSerializer, \
    ReportGenerator, ReportGeneratorSerializer, Project, ProjectSerializer, \
    DeploymentInstance, DeploymentInstanceSerializer, DeploymentDefinition, \
    DeploymentDefinitionSerializer
import modules.keycloak_lib as keylib


class ProjectPermission(BasePermission):

    def has_permission(self, request, view):
        """
        Should simply return, or raise a 403 response.
        """

        project = Project.objects.get(pk=view.kwargs['project_pk'])

        project_rules = {
            'GET': ['guest', 'member', 'admin'],
            'POST': ['member', 'admin'],
            'PUT': ['member', 'admin'],
            'DELETE': ['admin']
        }

        is_authorized = False
        if request.method in project_rules:
            is_authorized = keylib.keycloak_verify_user_role(request, project.slug, project_rules[request.method])

        print('Is authorized: {}'.format(is_authorized))
        return is_authorized


