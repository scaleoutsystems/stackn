from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.conf import settings
from kubernetes.client.rest import ApiException
import requests
import time
from projects.models import Project
from .models import Experiment
from projects.models import Environment
from .forms import ExperimentForm
from django.urls import reverse
import modules.keycloak_lib as keylib
from .experimentsauth import get_permissions
import logging

logger = logging.getLogger(__name__)

@login_required
def index(request, user, project):
    print('User: {}'.format(user))
    user_permissions = get_permissions(request, project)
    logger.info(user_permissions)
    if not user_permissions['view']:
        return HttpResponse('Not authorized', status=401)

    temp = 'experiments/index.html'

    project = Project.objects.filter(slug=project).first()
    print('Project: '+project.slug)
    experiments = Experiment.objects.filter(project=project).order_by('-created_at')
    environments = Environment.objects.all()

    return render(request, temp, locals())

        


@login_required
def run(request, user, project):
    user_permissions = get_permissions(request, project)
    if not user_permissions['create']:
        return HttpResponse('Not authorized', status=401)

    temp = 'experiments/run.html'
    project = Project.objects.filter(slug=project).first()
    deployment = None
    if request.method == "POST":
        form = ExperimentForm(request.POST)
        if form.is_valid():
            print("valid form! Saving")
            instance = Experiment()
            instance.username = user
            if not form.cleaned_data['schedule']:
                instance.schedule = "None"
            else:
                instance.schedule = form.cleaned_data['schedule']
            instance.command = form.cleaned_data['command']
            # environment = Environment.objects.get(pk=request.POST['environment'])
            instance.environment = form.cleaned_data['environment']
            instance.project = project
            instance.save()

            return HttpResponseRedirect(
                reverse('experiments:index', kwargs={'user': request.user, 'project': str(project.slug)}))
        else:
            print("FORM IS NOT VALID!")
    else:
        form = ExperimentForm()

    return render(request, temp, locals())

@login_required
def details(request, user, project, id):
    user_permissions = get_permissions(request, project)
    if not user_permissions['view']:
        return HttpResponse('Not authorized', status=401)

    temp = 'experiments/details.html'

    project = Project.objects.filter(slug=project).first()
    experiment = Experiment.objects.filter(id=id).first()

    try:
        url = settings.LOKI_SVC+'/loki/api/v1/query_range'
        query = {
          'query': '{type="cronjob", project="'+project.slug+'", app="'+experiment.helmchart.name+'"}',
          'limit': 50,
          'start': 0,
        }
        res = requests.get(url, params=query)
        res_json = res.json()['data']['result']
        logs = []
        for item in res_json:
            logline = ''
            for iline in item['values']:
                logs.append(iline[1])
            logs.append('--------------------')
    except ApiException as e:
        print(e)
        return HttpResponseRedirect(
            reverse('experiments:index', kwargs={'user': request.user, 'project': str(project.slug)}))

    return render(request, temp, locals())


@login_required
def delete(request, user, project, id):
    user_permissions = get_permissions(request, project)
    if not user_permissions['delete']:
        return HttpResponse('Not authorized', status=401)
    temp = 'experiments/index.html'
    instance = Experiment.objects.get(id=id)
    instance.helmchart.delete()
    return HttpResponseRedirect(
                reverse('experiments:index', kwargs={'user': user, 'project': project}))