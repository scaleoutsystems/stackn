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
            instance = form.save()
            from .jobs import run_job
            run_job(instance)
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
