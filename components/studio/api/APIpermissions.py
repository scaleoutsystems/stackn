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
        print(request.method)
        if request.method == 'GET':
            is_authorized = keylib.keycloak_verify_user_role(request, project.slug, ['guest', 'member', 'admin'])
            print('Is authorized: {}'.format(is_authorized))
            return is_authorized
        if request.method in ['POST', 'PUT']:
            is_authorized = keylib.keycloak_verify_user_role(request, project.slug, ['member', 'admin'])
            print('Is authorized: {}'.format(is_authorized))
            return is_authorized
        if request.method in ['DELETE']:
            is_authorized = keylib.keycloak_verify_user_role(request, project.slug, ['admin'])
            print('Is authorized: {}'.format(is_authorized))
            return is_authorized

        return False

