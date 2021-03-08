from django.shortcuts import render
from .models import ActivityLog
from projects.models import Project
from models.models import Model
from deployments.models import DeploymentInstance
from monitor.helpers import get_resource
from monitor.views import get_cpu_mem
from django.contrib.auth.decorators import login_required
from projects.helpers import delete_project_resources
from django.http import HttpResponseRedirect
from django.urls import reverse


@login_required
def index(request):
    activity_logs = ActivityLog.objects.filter(
        user=request.user).order_by('-created_at')[:5]

    return render(request, 'studio_admin_index.html', locals())


@login_required
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


@login_required
def load_lab_resources(request):
    template = "studio_admin_labs.html"

    objects = []
    projects = Project.objects.all()
    for proj in projects:
        labs = Session.objects.filter(project=proj)
        lab_list = get_cpu_mem(labs, proj.slug, 'lab')
        objects += lab_list

    return render(request, template, {'objects': objects})


@login_required
def load_deployment_resources(request):
    template = "studio_admin_deployments.html"

    objects = []
    projects = Project.objects.all()
    for proj in projects:
        deployments = DeploymentInstance.objects.filter(model__project=proj)
        deployment_list = get_cpu_mem(deployments, proj.slug, 'deployment')
        objects += deployment_list

    return render(request, template, {'objects': objects})


def remove_project(request, project_slug):
    if request.user.is_superuser:
        project = Project.objects.get(slug=project_slug)

        if project:
            project_id = project.pk
            retval = delete_project_resources(project)

            if not retval:
                print("Couldn't delete project!")
                return HttpResponseRedirect(reverse('studio_admin:project_resources'))
            
            models = Model.objects.filter(project=project)
            for model in models:
                model.status = 'AR'
                model.save()
            project.delete()

            print('Successfully de-allocated project resources!')

            log = ActivityLog(user=request.user, headline="Projects", description="Removed project #{}".format(project_id))
            log.save()

    return HttpResponseRedirect(reverse('studio_admin:project_resources'))


def remove_lab_session(request, session_uid):
    if request.user.is_superuser:
        session = Session.objects.get(id=session_uid)

        if session:
            session_id = session.pk
            session.helmchart.delete()

            log = ActivityLog(user=request.user, headline="Lab Sessions", description="Removed session #{}".format(session_id))
            log.save()

    return HttpResponseRedirect(reverse('studio_admin:lab_resources'))


def remove_deployment(request, model_id):
    if request.user.is_superuser:
        model = Model.objects.get(id=model_id)

        if model:
            di = DeploymentInstance.objects.get(model=model)

            if di:
                di_id = di.pk
                di.helmchart.delete()
                
                log = ActivityLog(user=request.user, headline="Deployments", description="Removed deployment #{}".format(di_id))
                log.save()

    return HttpResponseRedirect(reverse('studio_admin:deployment_resources'))
