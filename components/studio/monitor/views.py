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
from deployments.models import DeploymentInstance
from models.models import Model
from modules.project_auth import get_permissions


def get_cpu_mem(resources, project_slug, resource_type):
    res_list = list()
    for resource in resources:
        res_model = ''
        res_version = ''
        res_flavor = ''
        res_id = ''
        res_cpu_limit = get_resource(project_slug, resource_type, 'limits', 'cpu_cores', app_name=resource.appname)
        res_cpu_limit = "{:.2f}".format(float(res_cpu_limit))
        res_cpu_request = get_resource(project_slug, resource_type, 'requests', 'cpu_cores', app_name=resource.appname)
        res_cpu_limit = "{:.2f}".format(float(res_cpu_request))
        res_mem_limit = get_resource(project_slug, resource_type, 'limits', 'memory_bytes', app_name=resource.appname)
        res_mem_limit = "{:.2f}".format(float(res_mem_limit)/1e9*0.931323)
        res_mem_request = get_resource(project_slug, resource_type, 'requests', 'memory_bytes', app_name=resource.appname)
        res_mem_request = "{:.2f}".format(float(res_mem_request)/1e9*0.931323)
        
        if resource_type == 'lab':
            res_owner = resource.lab_session_owner.username
            res_flavor = resource.flavor_slug
            res_id = str(resource.id)

        elif resource_type == 'deployment':
            res_owner = resource.created_by
            res_model = resource.model.name
            res_version = resource.model.version
            res_id = resource.model.id
            
        res_list.append((res_owner, res_flavor, res_cpu_limit, res_cpu_request, res_mem_limit, res_mem_request, res_id, res_model, res_version))
    return res_list

@login_required(login_url='/accounts/login')
def overview(request, user, project):
    is_authorized = True
    user_permissions = get_permissions(request, project, sett.MONITOR_PERM)
    if not user_permissions['view']:
        request.session['oidc_id_token_expiration'] = -1
        request.session.save()
        # return HttpResponse('Not authorized', status=401)
        is_authorized = False
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
                elif tmp:
                    tmp = "{:.2f}".format(float(tmp))

                resource_status[resource_type][q_type][r_type] = tmp

    total_cpu = float(resource_status['lab']['limits']['cpu_cores'])+float(resource_status['deployment']['limits']['cpu_cores'])
    total_mem = float(resource_status['lab']['limits']['memory_bytes'])+float(resource_status['deployment']['limits']['memory_bytes'])
    total_cpu_req = float(resource_status['lab']['requests']['cpu_cores'])+float(resource_status['deployment']['requests']['cpu_cores'])
    total_mem_req = float(resource_status['lab']['requests']['memory_bytes'])+float(resource_status['deployment']['requests']['memory_bytes'])

    labs = Session.objects.filter(project=project)
    lab_list = get_cpu_mem(labs, project.slug, 'lab')
    
    deps = DeploymentInstance.objects.filter(model__project=project)
    dep_list = get_cpu_mem(deps, project.slug, 'deployment')
    print(dep_list)
    # lab_list = list()
    # for lab in labs:
    #     lab_cpu_limit = get_resource(project.slug, 'lab', 'limits', 'cpu_cores', app_name=lab.appname)
    #     lab_cpu_limit = "{:.2f}".format(float(lab_cpu_limit))
    #     lab_cpu_request = get_resource(project.slug, 'lab', 'requests', 'cpu_cores', app_name=lab.appname)
    #     lab_cpu_limit = "{:.2f}".format(float(lab_cpu_request))
    #     lab_mem_limit = get_resource(project.slug, 'lab', 'limits', 'memory_bytes', app_name=lab.appname)
    #     lab_mem_limit = "{:.2f}".format(float(lab_mem_limit)/1e9*0.931323)
    #     lab_mem_request = get_resource(project.slug, 'lab', 'requests', 'memory_bytes', app_name=lab.appname)
    #     lab_mem_request = "{:.2f}".format(float(lab_mem_request)/1e9*0.931323)
    #     lab_flavor = lab.flavor_slug
    #     lab_owner = lab.lab_session_owner.username
    #     lab_list.append((lab_owner, lab_flavor, lab_cpu_limit, lab_cpu_request, lab_mem_limit, lab_mem_request, str(lab.id)))

    return render(request, template, locals())

def delete_lab(request, user, project, uid):
    # project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first()
    # session = Session.objects.filter(Q(id=id), Q(project=project), Q(lab_session_owner=request.user)).first()
    user_permissions = get_permissions(request, project, sett.MONITOR_PERM)
    if not user_permissions['view']:
        request.session['oidc_id_token_expiration'] = -1
        request.session.save()
        return HttpResponse('Not authorized', status=401)
    project = Project.objects.get(slug=project)
    session = Session.objects.get(id=uid, project=project)
    if session:
        session.helmchart.delete()

    return HttpResponseRedirect(
        reverse('monitor:overview', kwargs={'user': request.user, 'project': str(project.slug)}))

def delete_deployment(request, user, project, model_id):
    user_permissions = get_permissions(request, project, sett.MONITOR_PERM)
    if not user_permissions['view']:
        request.session['oidc_id_token_expiration'] = -1
        request.session.save()
        return HttpResponse('Not authorized', status=401)
    model = Model.objects.get(id=model_id)
    instance = DeploymentInstance.objects.get(model=model)
    instance.helmchart.delete()
    return HttpResponseRedirect(reverse('monitor:overview', kwargs={'user': request.user, 'project': project}))

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