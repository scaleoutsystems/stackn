import uuid
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from projects.models import Project, ProjectLog
from reports.models import Report, ReportGenerator
from .models import Model, ModelLog, Metadata, ObjectType
from reports.forms import GenerateReportForm
from django.contrib.auth.decorators import login_required
import logging
from reports.helpers import populate_report_by_id, get_download_link
import markdown
import ast
from collections import defaultdict
from random import randint
from .helpers import get_download_url
from .forms import UploadModelImageForm

new_data = defaultdict(list)
logger = logging.getLogger(__name__)


def index(request):
    models = Model.objects.filter(access='PU', project__isnull=False).order_by('-uploaded_at')

    dtos = []
    for m in models:
        img_name = ""
        img_source = "default"
        if not m.img:
            img_id = randint(8, 13)
            img_name = "dist/img/patterns/image {}.png".format(img_id)
        else:
            img_name = m.img.url
            img_source = "custom"

        obj = {
            "pk": m.pk,
            "download_url": get_download_url(m.pk),
            "img_name": img_name,
            "img_source": img_source,
            "name": m.name,
            "description": m.description,
            "project_slug": m.project.slug
        }
        dtos.append(obj)

    return render(request, 'models_cards.html', locals())


@login_required
def list(request, user, project):
    menu = dict()
    menu['objects'] = 'active'
    template = 'models_list.html'
    project = Project.objects.get(slug=project)
    objects = []
    
    object_types = ObjectType.objects.all()
    for object_type in object_types:
        objects.append((object_type, Model.objects.filter(project=project, object_type__slug=object_type.slug)))
    print("OBJECTS")
    print(objects)
    active_type = 'model'

    return render(request, template, locals())


@login_required
def change_access(request, user, project, id):
    model = Model.objects.filter(pk=id).first()
    previous = model.get_access_display()

    if request.method == 'POST':
        visibility = request.POST.get('access', '')
        if visibility != model.access:
            model.access = visibility
            model.save()
            project_obj = Project.objects.get(slug=project)
            l = ProjectLog(project=project_obj, module='MO', headline='Model - {name}'.format(name=model.name),
                           description='Changed Access Level from {previous} to {current}'.format(previous=previous,
                                                                                                  current=model.get_access_display()))
            l.save()

    return HttpResponseRedirect(
        reverse('models:details_public', kwargs={'id': id}))


@login_required
def upload_image(request, user, project, id):
    if request.method == 'POST':
        form = UploadModelImageForm(request.POST, request.FILES)
        if form.is_valid():
            model = Model.objects.get(pk=id)
            model.img = request.FILES['file']
            model.save()

            project_obj = Project.objects.get(slug=project)
            l = ProjectLog(project=project_obj, module='MO', headline='Model - {name}'.format(name=model.name),
                           description='Uploaded new headline image.')
            l.save()

            return HttpResponseRedirect('/')
    else:
        form = UploadModelImageForm()

    return render(request, 'models_upload_image.html', {'form': form})


@login_required
def details(request, user, project, id):
    project = Project.objects.filter(slug=project).first()
    model = Model.objects.filter(id=id).first()
    model_access_choices = ['PU', 'PR', 'LI']
    model_access_choices.remove(model.access)
    deployments = DeploymentInstance.objects.filter(model=model)

    report_generators = ReportGenerator.objects.filter(project=project)

    unfinished_reports = Report.objects.filter(status='P').order_by('created_at')
    for report in unfinished_reports:
        populate_report_by_id(report.id)

    reports = Report.objects.filter(model__id=id, status='C').order_by('-created_at')

    report_dtos = []
    for report in reports:
        report_dtos.append({
            'id': report.id,
            'description': report.description,
            'created_at': report.created_at,
            'filename': get_download_link(project.pk, 'report_{}.json'.format(report.id))
        })

    if request.method == 'POST':
        file_path = None
        form = GenerateReportForm(request.POST)
        if form.is_valid():
            generator_id = int(form.cleaned_data['generator_file'])
            generator_object = ReportGenerator.objects.filter(pk=generator_id).first()

            file_path = 'reports/{}'.format(generator_object.generator)

            instance = {
                'id': str(uuid.uuid4()),
                'path_to_file': file_path,
                'model_uid': model.uid,
                'project_name': project.slug
            }

            new_report = Report(model=model, report="", job_id=instance['id'], generator=generator_object, status='P')
            new_report.save()

            l = ProjectLog(project=project, module='MO', headline='Model - {name}'.format(name=model.name),
                           description='Newly generated Metrics #{id}'.format(id=new_report.pk))
            l.save()

            from reports.jobs import run_job

            run_job(instance)

            return HttpResponseRedirect('/{}/{}/models/'.format(user, project.slug))
    else:
        form = GenerateReportForm()

    log_objects = ModelLog.objects.filter(project=project.name, trained_model=model)
    model_logs = []
    for log in log_objects:
        model_logs.append({
            'id': log.id,
            'trained_model': log.trained_model,
            'training_status': log.training_status,
            'training_started_at': log.training_started_at,
            'execution_time': log.execution_time,
            'code_version': log.code_version,
            'current_git_repo': log.current_git_repo,
            'latest_git_commit': log.latest_git_commit,
            'system_details': ast.literal_eval(log.system_details),
            'cpu_details': ast.literal_eval(log.cpu_details)
        })

    md_objects = Metadata.objects.filter(project=project.name, trained_model=model)
    if md_objects:
        metrics = get_chart_data(md_objects)

    filename = None
    readme = None
    import requests as r
    url = 'http://{}-file-controller/models/{}/readme'.format(project.slug, model.name)
    try:
        response = r.get(url)
        if response.status_code == 200 or response.status_code == 203:
            payload = response.json()
            if payload['status'] == 'OK':
                filename = payload['filename']

                md = markdown.Markdown(extensions=['extra'])
                readme = md.convert(payload['readme'])
    except Exception as e:
        logger.error("Failed to get response from {} with error: {}".format(url, e))

    return render(request, 'models_details.html', locals())

def get_chart_data(md_objects):
    new_data.clear()
    metrics_pre = []
    metrics = []
    for md_item in md_objects:
        metrics_pre.append({
            'run_id': md_item.run_id,
            'metrics': ast.literal_eval(md_item.metrics),
            'parameters': ast.literal_eval(md_item.parameters)
        })
    for m in metrics_pre: 
        for key, value in m["metrics"].items():
            new_data[key].append([m["run_id"], value, m["parameters"]])
    for key, value in new_data.items():
        data = []
        labels = []
        params = []
        run_id = []
        run_counter = 0
        for item in value:
            run_counter += 1
            labels.append("Run {}".format(run_counter))
            run_id.append(item[0])
            data.append(item[1])
            params.append(item[2])
        metrics.append({
            "metric": key,
            "details": {
                "run_id": run_id,
                "labels": labels,
                "data": data,
                "params": params
            }
        })
    return metrics


def details_public(request, id):
    model = Model.objects.filter(pk=id).first()

    model_access_choices = {'PU': 'Public', 'PR': 'Private', 'LI': 'Limited'}
    del model_access_choices[model.access]

    reports = Report.objects.filter(model__pk=id, status='C').order_by('-created_at')
    report_dtos = []
    for report in reports:
        report_dtos.append({
            'id': report.id,
            'description': report.description,
            'created_at': report.created_at,
            'filename': get_download_link(model.project.pk, 'report_{}.json'.format(report.id))
        })

    filename = None
    readme = None
    import requests as r
    url = 'http://{}-file-controller/models/{}/readme'.format(model.project.slug, model.name)
    try:
        response = r.get(url)
        if response.status_code == 200 or response.status_code == 203:
            payload = response.json()
            if payload['status'] == 'OK':
                filename = payload['filename']

                md = markdown.Markdown(extensions=['extra'])
                readme = md.convert(payload['readme'])
    except Exception as e:
        logger.error("Failed to get response from {} with error: {}".format(url, e))

    return render(request, 'models_details_public.html', locals())


@login_required
def delete(request, user, project, id):

    project = Project.objects.get(slug=project)
    model = Model.objects.get(id=id)

    l = ProjectLog(project=project, module='MO', headline='Model',
                    description='Model {name} has been removed'.format(name=model.name))
    l.save()

    model.delete()

    return HttpResponseRedirect(reverse('models:list', kwargs={'user':user, 'project':project.slug}))
