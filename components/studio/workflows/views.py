from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from projects.models import Project
from .models import WorkflowDefinition, WorkflowInstance
from .forms import WorkflowDefinitionForm, WorkflowInstanceForm
from django.urls import reverse


@login_required(login_url='/accounts/login')
def workflows_index(request, user, project):
    temp = 'workflow/list.html'

    project = Project.objects.filter(slug=project).first()
    definitions = WorkflowDefinition.objects.all()
    instances = WorkflowInstance.objects.all()

    return render(request, temp, locals())


@login_required(login_url='/accounts/login')
def workflows_run(request, user, project):
    temp = 'workflow/add.html'
    project = Project.objects.filter(slug=project).first()

    deployment = None
    if request.method == "POST":
        form = WorkflowInstanceForm(request.POST)
        if form.is_valid():
            print("valid form! Saving")
            instance = form.save()
            return HttpResponseRedirect(
                reverse('workflows:workflows_index', kwargs={'user': request.user, 'project': project.slug}))
        else:
            print("FORM IS NOT VALID!")
    else:
        form = WorkflowInstanceForm()

    return render(request, temp, locals())


@login_required(login_url='/accounts/login')
def workflows_details(request, user, project, id=None):
    temp = 'workflow/details.html'

    deployment = None

    if id:
        deployment = get_object_or_404(WorkflowInstance, pk=id)

    form = WorkflowInstanceForm(request.POST or None, instance=deployment)
    if request.method == "POST":
        if form.is_valid():
            print("valid form! Saving")
            form.save()
            return HttpResponseRedirect(reverse('workflows:workflows_index'))
        else:
            print("FORM IS NOT VALID!")

    return render(request, temp, locals())


@login_required(login_url='/accounts/login')
def workflows_definition_index(request):
    temp = 'definition/list.html'

    definitions = WorkflowDefinition.objects.all()

    return render(request, temp, locals())


@login_required(login_url='/accounts/login')
def workflows_definition_add(request):
    temp = 'definition/add.html'


    if request.method == "POST":
        form = WorkflowDefinitionForm(request.POST)
        if form.is_valid():
            print("valid form! Saving")
            form.save()
            return HttpResponseRedirect(reverse('workflows:workflows_definition_index'))
    else:
        form = WorkflowDefinitionForm()

    return render(request, temp, locals())


@login_required(login_url='/accounts/login')
def workflows_definition_edit(request, id=None):
    temp = 'definition/edit.html'

    deployment = None

    if id:
        deployment = get_object_or_404(WorkflowDefinition, pk=id)

    form = WorkflowDefinitionForm(request.POST or None, instance=deployment)
    if request.method == "POST":
        if form.is_valid():
            print("valid form! Saving")
            form.save()
            return HttpResponseRedirect(reverse('workflows:workflows_definition_index'))
        else:
            print("FORM IS NOT VALID!")

    return render(request, temp, locals())
