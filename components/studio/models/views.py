import uuid
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.db.models import Q
from django.core.files import File
from projects.models import Project, ProjectLog, Environment
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
from .forms import UploadModelCardHeadlineForm, EnvironmentForm
import modules.keycloak_lib as kc
from portal.models import PublicModelObject, PublishedModel

new_data = defaultdict(list)
logger = logging.getLogger(__name__)

def index(request,id=0):
    menu = dict()
    menu['models'] = 'active'
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
            except Exception as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'
            print(base_template)

    # create session object to store info about model and their tag counts
    if "model_tags" not in request.session:
        request.session['model_tags'] = {}
    # tag_count from the get request helps set num_tags which helps set the number of tags to show in the template
    if "tag_count" in request.GET:
        # add model id to model_tags object
        if "model_id_add" in request.GET:
            num_tags = int(request.GET['tag_count'])
            id=int(request.GET['model_id_add'])
            request.session['model_tags'][str(id)]=num_tags
        # remove model id from model_tags object
        if "model_id_remove" in request.GET:
            num_tags = int(request.GET['tag_count'])
            id=int(request.GET['model_id_remove'])
            if str(id) in request.session['model_tags']:
                request.session['model_tags'].pop(str(id))
    
    # reset model_tags if Model Tab on Sidebar pressed
    if id==0:
        if 'tf_add' not in request.GET and 'tf_remove' not in request.GET:
            request.session['model_tags'] = {}
    
    media_url = settings.MEDIA_URL
    published_models = PublishedModel.objects.all()
    
    # create session object to store ids for tag seacrh if it does not exist
    if "tag_filters" not in request.session:
        request.session['tag_filters'] = []
    if 'tf_add' in request.GET:
        tag = request.GET['tf_add']
        if tag not in request.session['tag_filters']:
            request.session['tag_filters'].append(tag)
    elif 'tf_remove' in request.GET:
        tag = request.GET['tf_remove']
        if tag in request.session['tag_filters']:
            request.session['tag_filters'].remove(tag)
    elif "tag_count"  not in request.GET:
        tag=""
        request.session['tag_filters'] = []
    print("tag_filters: ", request.session['tag_filters'])
    
    # changed list of published model only if tag filters are present
    if request.session['tag_filters']:
        tagged_published_models = []
        for model in published_models:
            model_objs = model.model_obj.order_by('-model__version')
            latest_model_obj = model_objs[0]
            mymodel = latest_model_obj.model
            for t in mymodel.tags.all():
                if t in request.session['tag_filters']:
                    tagged_published_models.append(model)
                    break
        published_models = tagged_published_models
        
    request.session.modified = True
    return render(request, 'models_cards.html', locals())


@login_required
def list(request, user, project):
    menu = dict()
    menu['objects'] = 'active'
    template = 'models_list.html'
    projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active')

    project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project).distinct().first()
    current_project = project.name
    objects = []
    
    models = Model.objects.filter(project=project).order_by('name', '-version').distinct('name')


    return render(request, template, locals())


@login_required
def unpublish_model(request, user, project, id):
    # TODO: Check that user has access to this particular model.
    model = Model.objects.get(pk=id)

    try:
        pmodel = PublishedModel.objects.get(name=model.name, project=model.project)
        pmos = pmodel.model_obj.all()
        pmos.delete()
        pmodel.delete()
    except Exception as err:
        print(err)
    model.access = "PR"
    model.save()
    return HttpResponseRedirect(reverse('models:list', kwargs={'user':user, 'project':project}))

@login_required
def publish_model(request, user, project, id):
    print("PUBLISHING MODEL")
    import s3fs
    import random
    from .helpers import add_pmo_to_publish
    # TODO: Check that user has access to this particular model.
    
    
    model = Model.objects.get(pk=id)
    print(model)
    # Default behavior is that all versions of a model are published.
    models = Model.objects.filter(name=model.name, project=model.project)
    
    
    img = settings.STATIC_ROOT+'dist/scilogo-green.png'
    img_file = open(img, 'rb')
    image = File(img_file)
    
    pmodel = PublishedModel(name=model.name, project=model.project)
    pmodel.save()
    img_uid = str(uuid.uuid1().hex)
    pmodel.img.save(img_uid, image)

    # Copy files to public location
    for mdl in models:
        add_pmo_to_publish(mdl, pmodel)
    
    model.access = "PU"
    model.save()

    return HttpResponseRedirect(reverse('models:list', kwargs={'user':user, 'project':project}))

    


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
def add_tag(request, published_id, id):
    model = Model.objects.filter(pk=id).first()
    previous = model.get_access_display()
    if request.method == 'POST':
        new_tag = request.POST.get('tag', '')
        print("New Tag: ",new_tag)
        model.tags.add(new_tag)
        model.save()
    return HttpResponseRedirect(reverse('models:details_public', kwargs={'id': published_id}))

@login_required
def remove_tag(request, published_id, id):
    model = Model.objects.filter(pk=id).first()
    previous = model.get_access_display()
    if request.method == 'POST':
        print(request.POST)
        new_tag = request.POST.get('tag', '')
        print("Remove Tag: ",new_tag)
        model.tags.remove(new_tag)
        model.save()

    return HttpResponseRedirect(reverse('models:details_public', kwargs={'id': published_id}))

@login_required
def add_tag_private(request, user, project, id):
    model = Model.objects.filter(pk=id).first()
    previous = model.get_access_display()
    if request.method == 'POST':
        new_tag = request.POST.get('tag', '')
        print("New Tag: ",new_tag)
        model.tags.add(new_tag)
        model.save()

    return HttpResponseRedirect(reverse('models:details_private', kwargs={'user':user, 'project':project, 'id':id}))


@login_required
def remove_tag_private(request, user, project, id):
    model = Model.objects.filter(pk=id).first()
    previous = model.get_access_display()
    if request.method == 'POST':
        print(request.POST)
        new_tag = request.POST.get('tag', '')
        print("Remove Tag: ",new_tag)
        model.tags.remove(new_tag)
        model.save()

    return HttpResponseRedirect(reverse('models:details_private', kwargs={'user':user, 'project':project, 'id':id}))

@login_required
def upload_model_headline(request, user, project, id):
    if request.method == 'POST':
        form = UploadModelCardHeadlineForm(request.POST, request.FILES)
        if form.is_valid():
            model = Model.objects.get(pk=id)
            model.model_card_headline = request.FILES['file']
            model.save()

            project_obj = Project.objects.get(slug=project)
            l = ProjectLog(project=project_obj, module='MO', headline='Model - {name}'.format(name=model.name),
                           description='Uploaded new headline image.')
            l.save()

            return HttpResponseRedirect('/')
    else:
        form = UploadModelCardHeadlineForm()

    return render(request, 'models_upload_headline.html', {'form': form})


@login_required
def add_docker_image(request, user, project, id):
    model = Model.objects.get(pk=id)

    if request.method == 'POST':
        form = EnvironmentForm(request.POST)

        if form.is_valid():
            registry = form.cleaned_data['registry']
            username = form.cleaned_data['username']
            repository = form.cleaned_data['repository']
            image = form.cleaned_data['image']
            tag = form.cleaned_data['tag']

            environment = Environment(
                name=registry+'/'+username,
                slug=None,
                project=model.project,
                repository=repository,
                image=image+':'+tag,
                registry=None,
                appenv=None,
                app=None
            )
            environment.save()

            model.docker_image = environment
            model.save()

            project_obj = Project.objects.get(slug=project)
            l = ProjectLog(project=project_obj, module='MO', headline='Model - {name}'.format(name=model.name),
                           description='Added reference to a Docker image.')
            l.save()

            return HttpResponseRedirect(
                reverse('models:details_public', kwargs={'id': id}))
    else:
        form = EnvironmentForm()

    return render(request, 'models_docker_image.html', {'form': form})


@login_required
def details(request, user, project, id):
    all_tags = Model.tags.tag_model.objects.all()
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


def import_model(request, id):
    print("IMPORTING MODEL")

@login_required
def details_private(request, user, project, id):
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active')
    except Exception as err:
        print("User not logged in.")
    base_template = 'base.html'

    project_slug = project
    is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
    if is_authorized:
        try:
            project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project_slug).first()
            base_template = 'baseproject.html'
        except Exception as err:
            project = []
            print(err)
        if not project:
            base_template = 'base.html'

    media_url = settings.MEDIA_URL
    # TODO: Check that user has access to this model (though already checked that user has access to project)
    model = Model.objects.get(pk=id) 
    all_tags = Model.tags.tag_model.objects.all()
    private = True
    print("MY TAGS: ",model.tags,user)
    # published_model = PublishedModel(pk=id)
    # model_objs = published_model.model_obj.order_by('-model__version')
    # latest_model_obj = model_objs[0]
    # model = latest_model_obj.model
    # print(model_objs)
    # print(latest_model_obj)

    return render(request, 'models_details_public.html', locals())

def details_public(request, id):
    private = False
    all_tags = Model.tags.tag_model.objects.all()
    print("Details tag ID:",id)
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
            except Exception as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'

    media_url = settings.MEDIA_URL
    published_model = PublishedModel(pk=id)
    print(published_model)
    model_objs = published_model.model_obj.order_by('-model__version')
    latest_model_obj = model_objs[0]
    model = latest_model_obj.model
    print(model_objs)
    print(latest_model_obj)

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
