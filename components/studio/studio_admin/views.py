from django.shortcuts import render
from datetime import datetime, timedelta
from .models import ActivityLog
from projects.models import Project

def index(request):
    activity_logs = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:5]

    return render(request, 'studio_admin_index.html', locals())

def load_module_objects(request, module):
    objects = []

    if module == 'projects':
        objects = load_projects()

    return render(request, 'studio_admin_module.html', {'objects': objects, 'module': module})

def load_projects():
    projects = Project.objects.all()
    return projects
