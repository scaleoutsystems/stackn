from django.http import HttpResponseRedirect
from projects.models import Project
from apps.models import AppInstance

from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.contrib.auth.models import User
from django.conf import settings

from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

@receiver(pre_save, sender=User)
def set_new_user_inactive(sender, instance, **kwargs):
    if instance._state.adding is True and settings.INACTIVE_USERS:
        print("Creating Inactive User")
        instance.is_active = False
    else:
        print("Updating User Record")

# Since this is a production feature, it will only work if DEBUG is set to False
def handle_page_not_found(request, exception):
    return HttpResponseRedirect('/')

class AccessPermission(BasePermission):

    def has_permission(self, request, view):
        """
        Should simply return, or raise a 403 response.
        """
        try:
            release = request.GET.get('release')
            app_instance = AppInstance.objects.get(parameters__contains={'release':release})
            project = app_instance.project
        except:
            project_slug = request.GET.get('project')
            project = Project.objects.get(slug=project_slug)
            return request.user.has_perm('can_view_project', project)
        
        if app_instance.access == "private":
            return app_instance.owner == request.user
        elif app_instance.access == "project":
            return request.user.has_perm('can_view_project', project)
        else:
            return True
class AuthView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated, AccessPermission]

    def get(self, request, format=None):
        content = {
            'user': str(request.user),
            'auth': str(request.auth),
        }
        return Response(content)