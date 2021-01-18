from django.shortcuts import render
from datetime import datetime, timedelta
from .models import ActivityLog
from projects.models import Project
from models.models import Model
from labs.models import Session
from deployments.models import DeploymentInstance

def index(request):
    str_projects = 'projects'
    str_models = 'models'
    str_labs = 'labs'
    str_deployments = 'deployments'

    activity_logs = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:5]

    return render(request, 'studio_admin_index.html', locals())

def load_module_objects(request, module):
    objects = None
    template = None

    if module == 'projects':
        objects = load_projects()
        template = "studio_admin_projects.html"
    if module == 'models':
        objects = load_models()
        template = "studio_admin_models.html"
    if module == 'labs':
        objects = load_labs()
        template = "studio_admin_labs.html"
    if module == 'deployments':
        objects = load_deployments()
        template = "studio_admin_deployments.html"

    return render(request, template, {'objects': objects})

def load_projects():
    projects = Project.objects.all()
    return projects

def load_models():
    models = Model.objects.all()
    return models

def load_labs():
    labs = Session.objects.all()
    return labs

def load_deployments():
    deployments = DeploymentInstance.objects.all()
    return deployments
