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
from .helpers import get_resource, get_all
from labs.models import Session


@login_required(login_url='/accounts/login')
def overview(request, user, project):
    template = 'monitor_overview.html'
    project = Project.objects.filter(slug=project).first()

    resource_types = ['lab', 'deployment']
    q_types = ['requests', 'limits']
    r_types = ['memory_bytes', 'cpu_cores']

    resource_status = dict()
    for resource_type in resource_types:
        resource_status[resource_type] = dict()
        for q_type in q_types:
            resource_status[resource_type][q_type] = dict()
            for r_type in r_types:
                tmp = get_resource(project.slug, resource_type, q_type, r_type)
                if r_type == 'memory_bytes':
                    tmp ="{:.2f}".format(float(tmp)/1e9*0.931323)
                else:
                    tmp = "{:.2f}".format(float(tmp))
                resource_status[resource_type][q_type][r_type] = tmp

    total_cpu = float(resource_status['lab']['limits']['cpu_cores'])+float(resource_status['deployment']['limits']['cpu_cores'])
    total_mem = float(resource_status['lab']['limits']['memory_bytes'])+float(resource_status['deployment']['limits']['memory_bytes'])

    labs = Session.objects.filter(project=project)
    for lab in labs:
        print(lab.lab_session_owner)

    # print(total_cpu)
    # print(total_mem)
    # print(get_all())

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