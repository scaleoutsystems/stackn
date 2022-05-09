from django.http import HttpResponseRedirect
from django.http import HttpResponse
from projects.models import Project

from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.contrib.auth.models import User
from django.conf import settings

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

def auth(request):
    if request.user.is_authenticated:
        project_slug = request.GET.get('project')
        project = Project.objects.get(slug=project_slug)
        if request.user.has_perm('can_view_project', project):
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=403)
    return HttpResponse(status=401)