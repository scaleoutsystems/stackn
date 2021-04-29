import os
from ast import literal_eval
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from projects.models import Project
from .models import DeploymentDefinition, DeploymentInstance
from .forms import DeploymentDefinitionForm, DeploymentInstanceForm, PredictForm, SettingsForm
from models.models import Model
from django.urls import reverse
from django.utils.text import slugify
import modules.keycloak_lib as keylib
from monitor.helpers import pod_up, get_count_over_time

@login_required
def predict(request, id, project):
    template = 'deploy/predict.html'
    is_authorized = False
    if request.user.is_authenticated and request.user and project is not None:
        proj_obj = Project.objects.get(slug=project)
        if proj_obj.owner == request.user:
            is_authorized = True
    print('Authorized: {}'.format(is_authorized))
    project = proj_obj
    deployment = DeploymentInstance.objects.get(id=id)
    model = deployment.model

    if request.method == 'POST': # and is_authorized:
        form = PredictForm(request.POST, request.FILES)
        if form.is_valid():
            import requests
            import json

            predict_url = 'https://{}{}{}/'.format(deployment.endpoint, deployment.path, deployment.deployment.path_predict)
            # print(predict_url)
            # Get user token
            # from rest_framework.authtoken.models import Token

            # token = Token.objects.get_or_create(user=request.user)
            kc = keylib.keycloak_init()
            token, refresh_token, token_url, public_key = keylib.keycloak_token_exchange_studio(kc, request.user.username)
            print('requesting: '+predict_url)
            res = requests.post(predict_url, files=form.files, headers={'Authorization':'Token '+token})
            print(res.text)
            try:
                prediction = json.loads(res.text)
                prediction = json.dumps(prediction, indent=4)
                if len(prediction) > 3000:
                    prediction = '{} ...(truncated remaining {} characters/'.format(prediction[0:300], len(prediction))
            except:
                prediction = res.text
    else:
        form = PredictForm()

    return render(request, template, locals())

@login_required
def deploy(request, id):
    model = Model.objects.get(id=id)
    print(request.user)
    if request.method == 'POST':
        deployment = request.POST.get('deployment', None)
        definition = DeploymentDefinition.objects.get(name=deployment)
        instance = DeploymentInstance(model=model, deployment=definition, created_by=request.user)
        instance.save()
        # return JsonResponse({"code": "201"})

    return HttpResponseRedirect(reverse('models:list', kwargs={'user':request.user, 'project':model.project.slug}))

@login_required
def serve_settings(request, id, project):
    # model = Model.objects.get(id=id)
    # print(request.user)
    
    template = 'deploy/settings.html'
    if request.user.is_authenticated and request.user and project is not None:
        proj_obj = Project.objects.get(slug=project)
        if proj_obj.owner == request.user:
            is_authorized = True


    project = proj_obj #Project.objects.get(slug=project)
    deployment = DeploymentInstance.objects.get(id=id)
    chart = deployment.helmchart
    params = literal_eval(chart.params)
    # Access keys with dot in Django template...
    replicas = params['replicas']
    cpu_limit = params['resources.limits.cpu']
    mem_limit = params['resources.limits.memory']
    cpu_request = params['resources.requests.cpu']
    mem_request = params['resources.requests.memory']
    # print(params)
    model = deployment.model
    if request.method == 'POST' and is_authorized:
        form = SettingsForm(request.POST)
        if form.is_valid():
            # print('Form is valid')
            params['replicas'] = request.POST.get('replicas', 1)
            params['resources.limits.cpu'] = request.POST.get('limits_cpu', 1000)
            params['resources.limits.memory'] = request.POST.get('limits_memory', 2048)
            params['resources.requests.cpu'] = request.POST.get('requests_cpu', 300)
            params['resources.requests.memory'] = request.POST.get('requests_memory', 1024)
            print(params)
            deployment.helmchart.params = params
            deployment.helmchart.save()
        else:
            print('Form is not valid; not updating settings.')
    form = SettingsForm(initial={'replicas': params['replicas'],
                                 'limits_cpu': params['resources.limits.cpu']})

    return render(request, template, locals())



@login_required
def undeploy(request, id):
    model = Model.objects.get(id=id)
    instance = DeploymentInstance.objects.get(model=model)
    instance.helmchart.delete()
    return HttpResponseRedirect(reverse('models:list', kwargs={'user':request.user, 'project':model.project.slug}))


def index(request):
    temp = 'deploy/cards.html'
    is_authorized = False

    deployments = DeploymentInstance.objects.filter(access=DeploymentInstance.PUBLIC)

    return render(request, temp, locals())


@login_required
def deployment_index(request, user, project):
    temp = 'deploy/list.html'

    is_authorized = False
    if request.user.is_authenticated and request.user and project is not None:
        is_authorized = True

    from projects.models import Project
    project = Project.objects.filter(slug=project).first()

    deployments = DeploymentInstance.objects.filter(model__project=project)
    deployment_status = []
    invocations = []
    for deployment in deployments:
        pods_up, pods_count = pod_up(deployment.appname)
        invocations.append(get_count_over_time('serve_predict_total',
                                               deployment.appname,
                                               deployment.deployment.path_predict,
                                               "200", "200y"))
        deployment_status.append([pods_up, pods_count])
    deploy_status = zip(deployments, deployment_status, invocations)

    return render(request, temp, locals())

@login_required
def deployment_edit(request, user, project, id=None):
    temp = 'deploy/edit.html'
    from projects.models import Project
    project = Project.objects.filter(slug=project).first()
    deployment = None

    if id:
        deployment = get_object_or_404(DeploymentInstance, pk=id)
        undeploy_model(deployment)

    form = DeploymentInstanceForm(request.POST or None, instance=deployment)
    if request.method == "POST":
        if form.is_valid():
            print("valid form! Saving")
            obj = form.save()

            deploy_model(obj)

            return HttpResponseRedirect(reverse('deployments:deployment_index'))
        else:
            print("FORM IS NOT VALID!")

    return render(request, temp, locals())


@login_required
def deployment_definition_index(request):
    temp = 'deploy/definition/list.html'

    definitions = DeploymentDefinition.objects.all()
    is_authorized = False

    return render(request, temp, locals())



@login_required
def deployment_definition_add(request):

    temp = 'deploy/definition/add.html'

    if request.method == "POST":
        form = DeploymentDefinitionForm(request.POST)
        if form.is_valid():
            print("valid form! Saving")
            form.save()
            return HttpResponseRedirect(reverse('deployments:deployment_definition_index'))
    else:
        form = DeploymentDefinitionForm()

    return render(request, temp, locals())


@login_required
def deployment_definition_edit(request, id=None):
    temp = 'deploy/definition/edit.html'

    deployment = None

    if id:
        deployment = get_object_or_404(DeploymentDefinition, pk=id)

    form = DeploymentDefinitionForm(request.POST or None, instance=deployment)
    if request.method == "POST":
        if form.is_valid():
            print("valid form! Saving")
            form.save()
            return HttpResponseRedirect(reverse('deployments:deployment_definition_index'))
        else:
            print("FORM IS NOT VALID!")

    return render(request, temp, locals())
