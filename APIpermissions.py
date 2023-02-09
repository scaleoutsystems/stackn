from rest_framework.permissions import BasePermission

from .serializers import Project


class ProjectPermission(BasePermission):
    def has_permission(self, request, view):
        """
        Should simply return, or raise a 403 response.
        """
        is_authorized = False
        project = Project.objects.get(pk=view.kwargs["project_pk"])

        # TODO: Check users project roles.
        if request.user == project.owner:
            is_authorized = True
        elif request.user in project.authorized.all():
            is_authorized = True
        print("Is authorized: {}".format(is_authorized))
        return is_authorized


class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        """
        Should simply return, or raise a 403 response.
        """
        is_authorized = False

        if request.user.is_superuser:
            is_authorized = True
        print("Is authorized: {}".format(is_authorized))
        return is_authorized
