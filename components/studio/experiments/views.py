from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from kubernetes.client.rest import ApiException

from projects.models import Project
from .models import Experiment
from projects.models import Environment
from .forms import ExperimentForm
from django.urls import reverse


@login_required(login_url='/accounts/login')
def index(request, user, project):
    temp = 'experiments/index.html'

    project = Project.objects.filter(slug=project).first()
    experiments = Experiment.objects.filter(project=project)
    environments = Environment.objects.all()

    return render(request, temp, locals())


@login_required(login_url='/accounts/login')
def run(request, user, project):
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

@login_required(login_url='/accounts/login')
def details(request, user, project, id):
    temp = 'experiments/details.html'

    project = Project.objects.filter(slug=project).first()
    experiment = Experiment.objects.filter(id=id).first()

    from .jobs import get_logs
    try:
        logs = get_logs(experiment)
    except ApiException as e:
        print(e)
        return HttpResponseRedirect(
            reverse('experiments:index', kwargs={'user': request.user, 'project': str(project.slug)}))

    return render(request, temp, locals())

@login_required(login_url='/accounts/login')
def delete(request, user, project, id):
    temp = 'experiments/index.html'
    instance = Experiment.objects.get(id=id)
    instance.helmchart.delete()
    return HttpResponseRedirect(
                reverse('experiments:index', kwargs={'user': user, 'project': project}))