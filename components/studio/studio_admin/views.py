from django.shortcuts import render
from .models import ActivityLog
from projects.models import Project
from models.models import Model
from django.db.models import Q
from monitor.helpers import get_resource
from monitor.views import get_cpu_mem
from django.contrib.auth.decorators import login_required
from projects.helpers import delete_project_resources
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests

from projects.views import delete_project as del_proj


@login_required
def index(request):
    menu = dict()
    menu['admin'] = 'active'
    activity_logs = ActivityLog.objects.filter(
        user=request.user).order_by('-created_at')[:5]

    projects = Project.objects.filter(status="active")

    return render(request, 'studio_admin_index.html', locals())

@login_required
def delete_project(request, project_slug):
    if request.user.is_superuser:
        project = Project.objects.get(slug=project_slug)
        del_proj(project)

    return HttpResponseRedirect(reverse('studio_admin:index'))