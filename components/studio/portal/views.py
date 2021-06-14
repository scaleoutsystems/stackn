import requests
import uuid
import time

from django.shortcuts import render, HttpResponseRedirect, reverse, redirect
from django.http import JsonResponse
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q
from django.template import engines
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

import modules.keycloak_lib as kc

from apps.models import Apps, AppInstance
from projects.models import Project

def index(request):
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active')
    except Exception as err:
        print("User not logged in.")
    base_template = 'base.html'
    if 'project' in request.session:
        project_slug = request.session['project']
        is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
        if is_authorized:
            try:
                project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project_slug).first()
                base_template = 'baseproject.html'
            except TypeError as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'
    # if project_selected:
    #     print("Project is selected")
    #     print(project)
    #     print(base_template)
    media_url = settings.MEDIA_URL

    published_apps = AppInstance.objects.filter(~Q(state='Deleted'), access='public')


    template = 'index_portal.html'
    return render(request, template, locals())
