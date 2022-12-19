import itertools
import time
from datetime import datetime

from apps.models import ResourceData
from django.conf import settings as sett
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse
from models.models import Model
from projects.models import Project

from .helpers import get_resource, get_total_cpu_usage_60s_ts


def get_cpu_mem(resources, project_slug, resource_type):
    res_list = list()
    for resource in resources:
        res_cpu_limit = get_resource(
            project_slug,
            resource_type,
            "limits",
            "cpu_cores",
            app_name=resource.appname,
        )
        res_cpu_limit = "{:.2f}".format(float(res_cpu_limit))
        res_cpu_request = get_resource(
            project_slug,
            resource_type,
            "requests",
            "cpu_cores",
            app_name=resource.appname,
        )
        res_cpu_limit = "{:.2f}".format(float(res_cpu_request))
        res_mem_limit = get_resource(
            project_slug,
            resource_type,
            "limits",
            "memory_bytes",
            app_name=resource.appname,
        )
        res_mem_limit = "{:.2f}".format(float(res_mem_limit) / 1e9 * 0.931323)
        res_mem_request = get_resource(
            project_slug,
            resource_type,
            "requests",
            "memory_bytes",
            app_name=resource.appname,
        )
        res_mem_request = "{:.2f}".format(
            float(res_mem_request) / 1e9 * 0.931323
        )

        if resource_type == "lab":
            res_owner = resource.lab_session_owner.username
            res_flavor = resource.flavor_slug
            res_id = str(resource.id)
            res_name = resource.name
            res_project = resource.project.name
            res_status = resource.status
            res_created = resource.created_at
            res_updated = resource.updated_at

            res_list.append(
                (
                    res_owner,
                    res_flavor,
                    res_cpu_limit,
                    res_cpu_request,
                    res_mem_limit,
                    res_mem_request,
                    res_id,
                    res_name,
                    res_project,
                    res_status,
                    res_created,
                    res_updated,
                )
            )

        elif resource_type == "deployment":
            res_owner = resource.created_by
            res_model = resource.model.name
            res_version = resource.model.version
            res_id = resource.model.id
            res_project = resource.deployment.project.name
            res_name = resource.deployment.name
            res_access = resource.access
            res_endpoint = resource.endpoint
            res_created = resource.created_at

            res_list.append(
                (
                    res_owner,
                    res_cpu_limit,
                    res_cpu_request,
                    res_mem_limit,
                    res_mem_request,
                    res_id,
                    res_model,
                    res_version,
                    res_project,
                    res_name,
                    res_access,
                    res_endpoint,
                    res_created,
                )
            )

    return res_list


@login_required
def liveout(request, user, project):
    is_authorized = True
    user_permissions = get_permissions(  # noqa: F821
        request, project, sett.MONITOR_PERM
    )

    if not user_permissions["view"]:
        request.session["oidc_id_token_expiration"] = -1
        request.session.save()
        # return HttpResponse('Not authorized', status=401)
        is_authorized = False
    template = "monitor2.html"
    project = Project.objects.filter(slug=project).first()

    return render(request, template, locals())


@login_required
def overview(request, user, project):
    try:
        projects = Project.objects.filter(
            Q(owner=request.user) | Q(authorized=request.user), status="active"
        ).distinct("pk")
    except TypeError as err:
        projects = []
        print(err)

    is_authorized = True
    user_permissions = get_permissions(  # noqa: F821
        request, project, sett.MONITOR_PERM
    )
    if not user_permissions["view"]:
        request.session["oidc_id_token_expiration"] = -1
        request.session.save()
        # return HttpResponse('Not authorized', status=401)
        is_authorized = False

    request.session["current_project"] = project
    template = "monitor_new.html"
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
    #             tmp = get_resource(project.slug, resource_type, q_type, r_type) # noqa E501

    #             if r_type == 'memory_bytes':
    #                 tmp ="{:.2f}".format(float(tmp)/1e9*0.931323)
    #             elif tmp:
    #                 tmp = "{:.2f}".format(float(tmp))

    #             resource_status[resource_type][q_type][r_type] = tmp

    # total_cpu = float(resource_status['lab']['limits']['cpu_cores'])+float(resource_status['deployment']['limits']['cpu_cores']) # noqa E501
    # total_mem = float(resource_status['lab']['limits']['memory_bytes'])+float(resource_status['deployment']['limits']['memory_bytes']) # noqa E501
    # total_cpu_req = float(resource_status['lab']['requests']['cpu_cores'])+float(resource_status['deployment']['requests']['cpu_cores']) # noqa E501
    # total_mem_req = float(resource_status['lab']['requests']['memory_bytes'])+float(resource_status['deployment']['requests']['memory_bytes']) # noqa E501

    # labs = Session.objects.filter(project=project)
    # lab_list = get_cpu_mem(labs, project.slug, 'lab')

    # deps = DeploymentInstance.objects.filter(model__project=project)
    # dep_list = get_cpu_mem(deps, project.slug, 'deployment')

    return render(request, template, locals())


def delete_lab(request, user, project, uid):
    # project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first() # noqa E501
    # session = Session.objects.filter(Q(id=id), Q(project=project), Q(lab_session_owner=request.user)).first() # noqa E501
    user_permissions = get_permissions(  # noqa F821
        request, project, sett.MONITOR_PERM
    )
    if not user_permissions["view"]:
        request.session["oidc_id_token_expiration"] = -1
        request.session.save()
        return HttpResponse("Not authorized", status=401)
    project = Project.objects.get(slug=project)
    session = Session.objects.get(id=uid, project=project)  # noqa F821
    if session:
        session.helmchart.delete()

    return HttpResponseRedirect(
        reverse(
            "monitor:overview",
            kwargs={"user": request.user, "project": str(project.slug)},
        )
    )


def delete_deployment(request, user, project, model_id):
    user_permissions = get_permissions(  # noqa F821
        request, project, sett.MONITOR_PERM
    )
    if not user_permissions["view"]:
        request.session["oidc_id_token_expiration"] = -1
        request.session.save()
        return HttpResponse("Not authorized", status=401)
    model = Model.objects.get(id=model_id)
    instance = DeploymentInstance.objects.get(model=model)  # noqa F821
    instance.helmchart.delete()
    return HttpResponseRedirect(
        reverse(
            "monitor:overview",
            kwargs={"user": request.user, "project": project},
        )
    )


def cpuchart(request, user, project, resource_type):
    # labels = ['a', 'b', 'c']
    # data = [1, 3, 2]
    labels = []
    data = []
    test = get_total_cpu_usage_60s_ts(project, resource_type)
    for value in test:
        tod = datetime.fromtimestamp(value[0]).strftime("%H:%M")
        labels.append(tod)
        data.append(value[1])
    return JsonResponse(
        data={
            "labels": labels,
            "data": data,
        }
    )


def usage(request, user, project):

    curr_timestamp = time.time()
    points = ResourceData.objects.filter(
        time__gte=curr_timestamp - 2 * 3600, appinstance__project__slug=project
    ).order_by("time")
    all_cpus = list()
    for point in points:
        all_cpus.append(point.cpu)
    total = (
        points.annotate(timeP=F("time"))
        .values("timeP")
        .annotate(total_cpu=Sum("cpu"), total_mem=Sum("mem"))
    )

    labels = list(total.values_list("timeP"))
    labels = list(itertools.chain.from_iterable(labels))
    step = 1
    np = 200
    if len(labels) > np:
        step = round(len(labels) / np)
    labels = labels[::step]
    x_data = list()
    for label in labels:
        x_data.append(datetime.fromtimestamp(label).strftime("%H:%M:%S"))

    total_mem = list(total.values_list("total_mem"))
    total_mem = list(itertools.chain.from_iterable(total_mem))[::step]

    total_cpu = list(total.values_list("total_cpu"))
    total_cpu = list(itertools.chain.from_iterable(total_cpu))[::step]

    return JsonResponse(
        data={"labels": x_data, "data_cpu": total_cpu, "data_mem": total_mem}
    )
