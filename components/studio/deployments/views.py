import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from projects.models import Project
from .models import DeploymentDefinition, DeploymentInstance
from .forms import DeploymentDefinitionForm, DeploymentInstanceForm, PredictForm
from models.models import Model
from django.urls import reverse


@login_required(login_url='/accounts/login')
def predict(request, id, project):
    template = 'deploy/predict.html'
    if request.user.is_authenticated and request.user and project is not None:
        is_authorized = True

    project = Project.objects.get(slug=project)
    deployment = DeploymentInstance.objects.get(id=id)
    model = deployment.model

    if request.method == 'POST':
        form = PredictForm(request.POST, request.FILES)
        if form.is_valid():
            import requests
            import json

            predict_url = 'https://{}/{}'.format(deployment.endpoint, deployment.deployment.path_predict)

            # Get user token
            from rest_framework.authtoken.models import Token

            token = Token.objects.get_or_create(user=request.user)

            res = requests.post(predict_url, files=form.files, headers={'Authorization':'Token '+token[0].key}, verify=False)
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

@login_required(login_url='/accounts/login')
def deploy(request, id):
    model = Model.objects.get(id=id)
    print(request.user)
    if request.method == 'POST':
        deployment = request.POST.get('deployment', None)
        definition = DeploymentDefinition.objects.get(name=deployment)
        instance = DeploymentInstance(model=model, deployment=definition)
        instance.save()
        # return JsonResponse({"code": "201"})

    return HttpResponseRedirect(reverse('models:list', kwargs={'user':request.user, 'project':model.project.slug}))


@login_required(login_url='/accounts/login')
def undeploy(request, id):
    model = Model.objects.get(id=id)
    instance = DeploymentInstance.objects.get(model=model)
    instance.delete()
    return HttpResponseRedirect(reverse('models:list', kwargs={'user':request.user, 'project':model.project.slug}))


def index(request):
    temp = 'deploy/cards.html'
    is_authorized = False

    deployments = DeploymentInstance.objects.filter(access=DeploymentInstance.PUBLIC)

    return render(request, temp, locals())


@login_required(login_url='/accounts/login')
def deployment_index(request, user, project):
    temp = 'deploy/list.html'

    is_authorized = False
    if request.user.is_authenticated and request.user and project is not None:
        is_authorized = True

    from projects.models import Project
    project = Project.objects.filter(slug=project).first()

    deployments = DeploymentInstance.objects.all()

    return render(request, temp, locals())

@login_required(login_url='/accounts/login')
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


@login_required(login_url='/accounts/login')
def deployment_definition_index(request):
    temp = 'deploy/definition/list.html'

    definitions = DeploymentDefinition.objects.all()
    is_authorized = False

    return render(request, temp, locals())



@login_required(login_url='/accounts/login')
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


@login_required(login_url='/accounts/login')
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
