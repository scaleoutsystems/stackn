import os

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404

from projects.models import Project
from .models import DeploymentDefinition, DeploymentInstance
from .forms import DeploymentDefinitionForm, DeploymentInstanceForm
from models.models import Model
from django.urls import reverse


@login_required(login_url='/accounts/login')
def deploy(request, id):
    model = Model.objects.filter(id=id).first()

    if request.method == 'POST':
        deployment = request.POST.get('deployment', None)
        definition = DeploymentDefinition.objects.filter(name=deployment).first()
        instance = DeploymentInstance(model=model, deployment=definition)

        # status = None
        # try:
        #     deploy_model(instance)
        # except Exception as e:
        #     print(e)
        #     status = '201'

        # if status:
        instance.save()

        return JsonResponse({"code": "201"})
    return HttpResponseRedirect(reverse('deployments:deployment_index'))


@login_required(login_url='/accounts/login')
def undeploy(request, id):
    model = Model.objects.get(id=id)
    instance = DeploymentInstance.objects.get(model=model)
    instance.delete()
    return JsonResponse({"code": "200"})


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
def deployment_add(request, user, project):
    temp = 'deploy/add.html'
    from projects.models import Project
    project = Project.objects.filter(slug=project).first()

    deployment = None
    if request.method == "POST":
        form = DeploymentInstanceForm(request.POST)
        if form.is_valid():
            print("valid form! Saving")
            obj = form.save()
            try:
                deploy_model(obj)
            except Exception as e:
                print(e)
                print("there was an error deploying")
            return HttpResponseRedirect(reverse('deployments:deployment_index', kwargs={'user':user, 'project':project.slug}))
    else:
        form = DeploymentInstanceForm()

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
