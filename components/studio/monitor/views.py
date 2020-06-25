from django.shortcuts import render, reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.conf import settings as sett
import logging

from datetime import datetime

from projects.models import Project
from .helpers import get_total_labs_cpu_usage_60s, get_total_labs_memory_usage_60s
from .helpers import get_labs_cpu_requests, get_labs_memory_requests
from .helpers import get_total_cpu_usage_60s_ts

@login_required(login_url='/accounts/login')
def overview(request, user, project):
    template = 'monitor_overview.html'
    project = Project.objects.filter(slug=project).first()

    labs_cpu_requests = get_labs_cpu_requests(project.slug)
    labs_memory_requests = get_labs_memory_requests(project.slug)
    labs_cpu_usage = get_total_labs_cpu_usage_60s(project.slug)
    labs_memory_usage = get_total_labs_memory_usage_60s(project.slug)

    return render(request, template, locals())

def cpuchart(request, user, project, resource_type):
    # labels = ['a', 'b', 'c']
    # data = [1, 3, 2]
    labels = []
    data = []
    test = get_total_cpu_usage_60s_ts(project, resource_type)
    for value in test:
        tod = datetime.fromtimestamp(value[0]).strftime('%H:%M')
        labels.append(tod)
        data.append(value[1])
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })