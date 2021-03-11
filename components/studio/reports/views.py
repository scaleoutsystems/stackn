import os
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from projects.models import Project, ProjectLog
from .forms import ReportGeneratorForm
from .models import Report, ReportGenerator
from django.db.models import Q
from .helpers import get_visualiser_file
import logging

logger = logging.getLogger(__name__)


@login_required
def index(request, user, project):
    template = 'reports_list.html'

    project = Project.objects.filter(slug=project).first()
    reports = ReportGenerator.objects.filter(project=project).order_by('-created_at')

    return render(request, template, locals())


@login_required
def add(request, user, project):
    project = Project.objects.filter(slug=project).first()

    url = 'http://{}-file-controller/reports'.format(project.slug)
    import requests
    report_generators = []
    try:
        response = requests.get(url)
        if response.status_code == 200 or response.status_code == 203:
            payload = response.json()
            if payload['status'] == 'OK':
                for file in payload['generators']:
                    report_generators.append(file['name'])
    except Exception as e:
        logger.error("Failed to get response from {} with error: {}".format(url, e))

    if request.method == 'POST':
        form = ReportGeneratorForm(request.POST)

        if form.is_valid():
            obj = form.save()

            l = ProjectLog(project=project, module='RE', headline='Metrics',
                           description='A new Generator {id} has been added'.format(id=obj.pk))
            l.save()

            get_visualiser_file(project.pk, obj.visualiser)

            url = '/{}/{}/reports/{}'.format(request.user, project.slug, obj.pk)
        else:
            url = '/{}/{}/reports/'.format(request.user, project.slug)

        return HttpResponseRedirect(url)
    else:
        form = ReportGeneratorForm({'project': project.id})

    return render(request, 'reports_add.html', locals())


@login_required
def details(request, user, project, id):
    template = 'reports_details_generator.html'

    project = Project.objects.filter(slug=project).first()
    report = ReportGenerator.objects.filter(id=id).first()

    return render(request, template, locals())


@login_required
def visualize_report(request, user, project, id):
    template = 'reports_details.html'

    project = Project.objects.filter(slug=project).first()
    report = Report.objects.filter(id=id).first()

    filename = 'report_{}.png'.format(id)

    reports_compare = Report.objects.filter(~Q(id=id))

    return render(request, template, locals())


def visualize_report_public(request, id):
    template = 'reports_details_public.html'

    report = Report.objects.filter(pk=id).first()

    filename = 'report_{}.png'.format(id)

    reports_compare = Report.objects.filter(~Q(id=id))

    return render(request, template, locals())


@login_required
def delete_generator(request, user, project, id):
    project = Project.objects.get(slug=project)
    report = ReportGenerator.objects.get(id=id)

    path = 'reports/{}'.format(report.visualiser)

    if os.path.exists(path):
        os.unlink(path)

    l = ProjectLog(project=project, module='RE', headline='Metrics',
                    description='Generator {id} has been removed'.format(id=report.pk))
    l.save()

    report.delete()

    return HttpResponseRedirect('/{}/{}/reports/'.format(request.user, project.slug))


@login_required
def delete_report(request, user, project, id):
    project = Project.objects.filter(slug=project).first()
    report = Report.objects.filter(id=id).first()

    path = 'reports/report_{}.png'.format(id)

    if request.method == "POST":
        if os.path.exists(path):
            os.unlink(path)

        l = ProjectLog(project=project, module='RE', headline='Metrics',
                       description='Metrics {id} has been removed'.format(id=report.pk))
        l.save()

        report.delete()

        return HttpResponseRedirect('/{}/{}/models/'.format(request.user, project.slug))

    return render(request, 'report_confirm_delete.html', locals())
