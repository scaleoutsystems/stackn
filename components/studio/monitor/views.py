from django.shortcuts import render, reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.conf import settings as sett
import logging
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import time
from django.db.models import Count, Sum, F
import itertools

from projects.models import Project
from .helpers import get_total_labs_cpu_usage_60s, get_total_labs_memory_usage_60s
from .helpers import get_labs_cpu_requests, get_labs_memory_requests
from .helpers import get_total_cpu_usage_60s_ts
from .helpers import get_resource, get_all
# from deployments.models import DeploymentInstance
from models.models import Model
from apps.models import AppInstance, ResourceData
from modules.project_auth import get_permissions
import pytz

def get_cpu_mem(resources, project_slug, resource_type):
    res_list = list()
    for resource in resources:
        res_cpu_limit = get_resource(
            project_slug, resource_type, 'limits', 'cpu_cores', app_name=resource.appname)
        res_cpu_limit = "{:.2f}".format(float(res_cpu_limit))
        res_cpu_request = get_resource(
            project_slug, resource_type, 'requests', 'cpu_cores', app_name=resource.appname)
        res_cpu_limit = "{:.2f}".format(float(res_cpu_request))
        res_mem_limit = get_resource(
            project_slug, resource_type, 'limits', 'memory_bytes', app_name=resource.appname)
        res_mem_limit = "{:.2f}".format(float(res_mem_limit)/1e9*0.931323)
        res_mem_request = get_resource(
            project_slug, resource_type, 'requests', 'memory_bytes', app_name=resource.appname)
        res_mem_request = "{:.2f}".format(float(res_mem_request)/1e9*0.931323)

        if resource_type == 'lab':
            res_owner = resource.lab_session_owner.username
            res_flavor = resource.flavor_slug
            res_id = str(resource.id)
            res_name = resource.name
            res_project = resource.project.name
            res_status = resource.status
            res_created = resource.created_at
            res_updated = resource.updated_at

            res_list.append((res_owner, res_flavor, res_cpu_limit, res_cpu_request, res_mem_limit,
                             res_mem_request, res_id, res_name, res_project, res_status, res_created, res_updated))

        elif resource_type == 'deployment':
            res_owner = resource.created_by
            res_model = resource.model.name
            res_version = resource.model.version
            res_id = resource.model.id
            res_project = resource.deployment.project.name
            res_name = resource.deployment.name
            res_access = resource.access
            res_endpoint = resource.endpoint
            res_created = resource.created_at

            res_list.append((res_owner, res_cpu_limit, res_cpu_request, res_mem_limit, res_mem_request,
                             res_id, res_model, res_version, res_project, res_name, res_access, res_endpoint, res_created))

    return res_list


@login_required
def liveout(request, user, project):
    is_authorized = True
    user_permissions = get_permissions(request, project, sett.MONITOR_PERM)
    
    if not user_permissions['view']:
        request.session['oidc_id_token_expiration'] = -1
        request.session.save()
        # return HttpResponse('Not authorized', status=401)
        is_authorized = False
    template = 'monitor2.html'
    project = Project.objects.filter(slug=project).first()


    return render(request, template, locals())

@login_required
def overview(request, user, project):
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active').distinct('pk')
    except TypeError as err:
        projects = []
        print(err)

    is_authorized = True
    user_permissions = get_permissions(request, project, sett.MONITOR_PERM)
    if not user_permissions['view']:
        request.session['oidc_id_token_expiration'] = -1
        request.session.save()
        # return HttpResponse('Not authorized', status=401)
        is_authorized = False
    
    request.session['current_project'] = project
    template = 'monitor_new.html'
    project = Project.objects.filter(slug=project).first()

    # resource_types = ['lab', 'deployment']
    # q_types = ['requests', 'limits']
    # r_types = ['memory_bytes', 'cpu_cores']

    # resource_status = dict()
    # for resource_type in resource_types:
    #     resource_status[resource_type] = dict()
    #     for q_type in q_types:
    #         resource_status[resource_type][q_type] = dict()
    #         for r_type in r_types:
    #             tmp = get_resource(project.slug, resource_type, q_type, r_type)
                
    #             if r_type == 'memory_bytes':
    #                 tmp ="{:.2f}".format(float(tmp)/1e9*0.931323)
    #             elif tmp:
    #                 tmp = "{:.2f}".format(float(tmp))

    #             resource_status[resource_type][q_type][r_type] = tmp

    # total_cpu = float(resource_status['lab']['limits']['cpu_cores'])+float(resource_status['deployment']['limits']['cpu_cores'])
    # total_mem = float(resource_status['lab']['limits']['memory_bytes'])+float(resource_status['deployment']['limits']['memory_bytes'])
    # total_cpu_req = float(resource_status['lab']['requests']['cpu_cores'])+float(resource_status['deployment']['requests']['cpu_cores'])
    # total_mem_req = float(resource_status['lab']['requests']['memory_bytes'])+float(resource_status['deployment']['requests']['memory_bytes'])

    # labs = Session.objects.filter(project=project)
    # lab_list = get_cpu_mem(labs, project.slug, 'lab')
    
    # deps = DeploymentInstance.objects.filter(model__project=project)
    # dep_list = get_cpu_mem(deps, project.slug, 'deployment')


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


@csrf_exempt
def usage(request, user, project):
    
    tz = pytz.timezone('Europe/Stockholm')
    curr_timestamp = time.time()
    print("Query")
    start = time.process_time()
    points = ResourceData.objects.filter(time__gte=curr_timestamp-2*3600, appinstance__project__slug=project).order_by('time')
    print("Query end :",time.process_time() - start)
    # print(list(points.all()))
    # all_cpus = list()
    # for point in points:
    #     print(point)
    #     all_cpus.append(point.cpu)
    
    # print("NUMBER OF POINTS")
    # print(len(all_cpus))
    # print("MAX:")
    # print(max(all_cpus))
    # print("ALLL CPUS: ",all_cpus)
    print("Annotate")
    start = time.process_time()
    total = points.annotate(timeP=F('time')).values('timeP').annotate(total_cpu=Sum('cpu'), total_mem=Sum('mem'))
    print("Annotate End: ",time.process_time() - start)
    # print(total)
    
    labels = list(total.values_list('timeP'))
    labels = list(itertools.chain.from_iterable(labels))
    step = 1
    np = 200
    if len(labels) > np:
        step = round(len(labels)/np)
    labels = labels[::step]
    x_data = list()
    print("Labels")
    start = time.process_time()
    for label in labels:
        # print(datetime.fromtimestamp(label,tz).strftime('%H:%M:%S'),"---",label,"---",datetime.fromtimestamp(label,tz))
        x_data.append(datetime.fromtimestamp(label,tz).strftime('%H:%M:%S'))
    print("Labels end: ",time.process_time() - start)  
    total_mem = list(total.values_list('total_mem'))
    total_mem = list(itertools.chain.from_iterable(total_mem))[::step]
    
    total_cpu= list(total.values_list('total_cpu'))
    # print("MAX CPU")
    # print(max(total_cpu))
    total_cpu = list(itertools.chain.from_iterable(total_cpu))[::step]
    # print("MAX CPU")
    # print(max(total_cpu))
    
    # print(len(total_cpu))
    return JsonResponse(data={
        'labels': x_data,
        'data_cpu': total_cpu,
        'data_mem': total_mem
    })