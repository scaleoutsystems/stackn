from django.shortcuts import render
from datetime import datetime, timedelta
from .models import ActivityLog
from projects.models import Project
from models.models import Model
from labs.models import Session
from deployments.models import DeploymentInstance
from monitor.helpers import get_resource
from django.template.defaulttags import register
from monitor.views import get_cpu_mem


def index(request):
    activity_logs = ActivityLog.objects.filter(
        user=request.user).order_by('-created_at')[:5]

    return render(request, 'studio_admin_index.html', locals())


def load_project_resources(request):
    template = "studio_admin_projects.html"

    objects = Project.objects.all()

    resource_types = ['lab', 'deployment']
    q_types = ['requests', 'limits']
    r_types = ['memory_bytes', 'cpu_cores']

    projects_resources = dict()
    for project in objects:
        projects_resources[project.slug] = dict()
        for resource_type in resource_types:
            projects_resources[project.slug][resource_type] = dict()
            for q_type in q_types:
                projects_resources[project.slug][resource_type][q_type] = dict()
                for r_type in r_types:
                    tmp = get_resource(
                        project.slug, resource_type, q_type, r_type)

                    if r_type == 'memory_bytes':
                        tmp = "{:.2f}".format(float(tmp)/1e9*0.931323)
                    elif tmp:
                        tmp = "{:.2f}".format(float(tmp))

                    projects_resources[project.slug][resource_type][q_type][r_type] = tmp

        projects_resources[project.slug]['total_cpu'] = float(projects_resources[project.slug]['lab']['limits']['cpu_cores'])+float(
            projects_resources[project.slug]['deployment']['limits']['cpu_cores'])
        projects_resources[project.slug]['total_mem'] = float(projects_resources[project.slug]['lab']['limits']['memory_bytes'])+float(
            projects_resources[project.slug]['deployment']['limits']['memory_bytes'])
        projects_resources[project.slug]['total_cpu_req'] = float(projects_resources[project.slug]['lab']['requests']['cpu_cores'])+float(
            projects_resources[project.slug]['deployment']['requests']['cpu_cores'])
        projects_resources[project.slug]['total_mem_req'] = float(projects_resources[project.slug]['lab']['requests']['memory_bytes'])+float(
            projects_resources[project.slug]['deployment']['requests']['memory_bytes'])

    return render(request, template, locals())


@register.filter
def get_resource_value(projects_resources, args):
    arg_list = [arg.strip() for arg in args.split(',')]

    project_slug = arg_list[0]

    if len(arg_list) == 2:
        total_x = arg_list[1]
        return projects_resources[project_slug][total_x]

    resource_type = arg_list[1]
    q_type = arg_list[2]
    r_type = arg_list[3]

    return projects_resources[project_slug][resource_type][q_type][r_type]


def load_lab_resources(request):
    template = "studio_admin_labs.html"

    objects = []
    projects = Project.objects.all()
    for proj in projects:
        labs = Session.objects.filter(project=proj)
        lab_list = get_cpu_mem(labs, proj.slug, 'lab')
        objects += lab_list

    return render(request, template, {'objects': objects})


def load_deployment_resources(request):
    template = "studio_admin_deployments.html"

    objects = []
    projects = Project.objects.all()
    for proj in projects:
        deployments = DeploymentInstance.objects.filter(model__project=proj)
        deployment_list = get_cpu_mem(deployments, proj.slug, 'deployment')
        objects += deployment_list

    return render(request, template, {'objects': objects})
