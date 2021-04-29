from django.shortcuts import render, reverse
from .models import Project, Environment, ProjectLog
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from .exceptions import ProjectCreationException
from .helpers import delete_project_resources
from django.contrib.auth.models import User
from django.conf import settings as sett
import logging
import markdown
import time
from .forms import TransferProjectOwnershipForm, PublishProjectToGitHub
from django.db.models import Q
from models.models import Model
import requests as r
import base64
from projects.helpers import get_minio_keys
from .models import Project, S3, Flavor, ProjectTemplate, MLFlow
from .forms import FlavorForm
from apps.models import AppInstance, AppCategories
from apps.models import Apps
import modules.keycloak_lib as kc
from datetime import datetime, timedelta
from modules.project_auth import get_permissions
from .helpers import create_project_resources
from .tasks import create_resources_from_template
from models.models import Model
# from deployments.models import DeploymentInstance
from apps.views import get_status_defs

logger = logging.getLogger(__name__)


def index(request):
    template = 'index_projects.html'
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active').distinct('pk')
    except TypeError as err:
        projects = []
        print(err)

    request.session['next'] = '/projects/'
    return render(request, template, locals())

@login_required
def create_environment(request, user, project_slug):
    template = 'create_environment.html'
    project = Project.objects.get(slug=project_slug)
    action = "Create"

    apps = Apps.objects.all()

    return render(request, template, locals())

@login_required
def environments(request, user, project_slug):
    template = 'environments.html'
    project = Project.objects.get(slug=project_slug)

    return render(request, template, locals())


@login_required
def settings(request, user, project_slug):
    user_permissions = get_permissions(request, project_slug, sett.PROJECT_SETTINGS_PERM)
    print(user_permissions)
    template = 'settings.html'
    project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), Q(slug=project_slug)).first()
    url_domain = sett.DOMAIN
    platform_users = User.objects.filter(~Q(pk=project.owner.pk))
    environments = Environment.objects.filter(project=project)
    apps = Apps.objects.all()

    s3instances = S3.objects.filter(project=project)
    flavors = Flavor.objects.filter(project=project)
    mlflows = MLFlow.objects.filter(project=project)

    if request.method == 'POST':
        form = TransferProjectOwnershipForm(request.POST)
        if form.is_valid():
            new_owner_id = int(form.cleaned_data['transfer_to'])
            new_owner = User.objects.filter(pk=new_owner_id).first()
            project.owner = new_owner
            project.save()

            l = ProjectLog(project=project, module='PR', headline='Project owner',
                           description='Transferred Project ownership to {owner}'.format(owner=project.owner.username))
            l.save()

            return HttpResponseRedirect('/projects/')
    else:
        form = TransferProjectOwnershipForm()

    return render(request, template, locals())

@login_required
def change_description(request, user, project_slug):
    project = Project.objects.filter(slug=project_slug).first()

    if request.method == 'POST':
        description = request.POST.get('description', '')
        if description != '':
            project.description = description
            project.save()

            l = ProjectLog(project=project, module='PR', headline='Project description',
                           description='Changed description for project')
            l.save()
        # TODO fix the create_environment_image creation

    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': request.user, 'project_slug': project.slug}))

@login_required
def create_environment(request, user, project_slug):
    # TODO: Ensure that user is allowed to create environment in this project.
    if request.method == 'POST':
        project = Project.objects.get(slug=project_slug)
        name = request.POST.get('environment_name')
        repo = request.POST.get('environment_repository')
        image = request.POST.get('environment_image')
        app_pk = request.POST.get('environment_app')
        app = Apps.objects.get(pk=app_pk)
        environment = Environment(name=name, slug=name, project=project, repository=repo, image=image, app=app)
        environment.save()
    return HttpResponseRedirect(reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def delete_environment(request, user, project_slug):
    if request.method == "POST":
        project = Project.objects.get(slug=project_slug)
        pk = request.POST.get('environment_pk')
        # TODO: Check that the user has permission to delete this environment.
        environment = Environment.objects.get(pk=pk, project=project)
        environment.delete()
    
    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def create_flavor(request, user, project_slug):
    # TODO: Ensure that user is allowed to create flavor in this project.
    if request.method == 'POST':
        # TODO: Check input
        project = Project.objects.get(slug=project_slug)
        print(request.POST)
        name = request.POST.get('flavor_name')
        cpu_req = request.POST.get('cpu_req')
        mem_req = request.POST.get('mem_req')
        gpu_req = request.POST.get('gpu_req')
        cpu_lim = request.POST.get('cpu_lim')
        mem_lim = request.POST.get('mem_lim')
        flavor = Flavor(name=name,
                        project=project,
                        cpu_req=cpu_req,
                        mem_req=mem_req,
                        gpu_req=gpu_req,
                        cpu_lim=cpu_lim,
                        mem_lim=mem_lim)
        flavor.save()
    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def delete_flavor(request, user, project_slug):
    if request.method == "POST":
        project = Project.objects.get(slug=project_slug)
        pk = request.POST.get('flavor_pk')
        # TODO: Check that the user has permission to delete this flavor.
        flavor = Flavor.objects.get(pk=pk, project=project)
        flavor.delete()
    
    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def set_s3storage(request, user, project_slug, s3storage=[]):
    # TODO: Ensure that the user has the correct permissions to set this specific
    # s3 object to storage in this project (need to check that the user has access to the
    # project as well.)
    if request.method == 'POST' or s3storage:
        project = Project.objects.get(slug=project_slug)
        
        if s3storage:
            s3obj = S3.objects.get(name=s3storage, project=project)
        else:
            pk = request.POST.get('s3storage')
            if pk == 'blank':
                s3obj = None
            else:
                s3obj = S3.objects.get(pk=pk)

        project.s3storage = s3obj
        project.save()

        if s3storage:
            return JsonResponse({"status": "ok"})

    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def set_mlflow(request, user, project_slug, mlflow=[]):
    # TODO: Ensure that the user has the correct permissions to set this specific
    # MLFlow object to MLFlow Server in this project (need to check that the user has access to the
    # project as well.)
    if request.method == 'POST' or mlflow:
        project = Project.objects.get(slug=project_slug)
        
        if mlflow:
            mlflowobj = MLFlow.objects.get(name=mlflow, project=project)
        else:
            pk = request.POST.get('mlflow')
            mlflowobj = MLFlow.objects.get(pk=pk)

        project.mlflow = mlflowobj
        project.save()

        if mlflow:
            return JsonResponse({"status": "ok"})

    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def grant_access_to_project(request, user, project_slug):

    project = Project.objects.get(slug=project_slug)

    if request.method == 'POST':

        selected_users = request.POST.getlist('selected_users')

        l = ProjectLog(project=project, module='PR', headline='New members',
                       description='{number} new members have been added to the Project'.format(
                           number=len(selected_users)))
        l.save()

        if len(selected_users) == 1:
            selected_users = list(selected_users)

        for selected_user in selected_users:
            user_tmp = User.objects.get(pk=selected_user)
            project.authorized.add(user_tmp)
            username_tmp = user_tmp.username
            logger.info('Trying to add user {} to project.'.format(username_tmp))
            kc.keycloak_add_role_to_user(project.slug, username_tmp, 'member')

    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def revoke_access_to_project(request, user, project_slug):

    project = Project.objects.get(slug=project_slug)

    if request.method == 'POST':

        selected_users = request.POST.getlist('selected_users')

        l = ProjectLog(project=project, module='PR', headline='Removed Project members',
                       description='{number} of members have been removed from the Project'.format(
                           number=len(selected_users)))
        l.save()

        if len(selected_users) == 1:
            selected_users = list(selected_users)

        for selected_user in selected_users:
            user_tmp = User.objects.get(pk=selected_user)
            project.authorized.remove(user_tmp)
            username_tmp = user_tmp.username
            logger.info('Trying to add user {} to project.'.format(username_tmp))
            kc.keycloak_remove_role_from_user(project.slug, username_tmp, 'member')

    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required
def create(request):
    template = 'project_create.html'
    templates = ProjectTemplate.objects.all()

    if request.method == 'POST':

        success = True

        name = request.POST.get('name', 'default')
        access = request.POST.get('access', 'org')
        description = request.POST.get('description', '')
        repository = request.POST.get('repository', '')
        
        # Try to create database project object.
        try:
            project = Project.objects.create_project(name=name,
                                                     owner=request.user,
                                                     description=description,
                                                     repository=repository)
        except ProjectCreationException as e:
            print("ERROR: Failed to create project database object.")
            success = False

        try:
            # Create project resources (Keycloak only)
            create_project_resources(project, request.user.username, repository)

            # Create resources from the chosen template
            project_template = ProjectTemplate.objects.get(pk=request.POST.get('project-template'))
            create_resources_from_template.delay(request.user.username, project.slug, project_template.template)

            # Reset user token
            request.session['oidc_id_token_expiration'] = time.time()-100
            request.session.save()
        except ProjectCreationException as e:
            print("ERROR: could not create project resources")
            success = False

        if not success:
            project.delete()
        else:
            l1 = ProjectLog(project=project, module='PR', headline='Project created',
                            description='Created project {}'.format(project.name))
            l1.save()

            l2 = ProjectLog(project=project, module='PR', headline='Getting started',
                            description='Getting started with project {}'.format(project.name))
            l2.save()

        next_page = request.POST.get('next', '/{}/{}'.format(request.user, project.slug))

        return HttpResponseRedirect(next_page, {'message': 'Created project'})

    
    return render(request, template, locals())


@login_required
def details(request, user, project_slug):

    is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
    
    template = 'project.html'

    url_domain = sett.DOMAIN

    project = None
    message = None
    username = request.user.username
    try:
        owner = User.objects.filter(username=username).first()
        project = Project.objects.filter(Q(owner=owner) | Q(authorized=owner), Q(slug=project_slug)).first()
    except Exception as e:
        message = 'Project not found.'

    if project:
        pk_list = ''
        
        status_success, status_warning = get_status_defs()
        activity_logs = ProjectLog.objects.filter(project=project).order_by('-created_at')[:5]
        resources = list()
        cats = AppCategories.objects.all()
        rslugs = []
        for cat in cats:
            rslugs.append({"slug": cat.slug, "name": cat.name})

        for rslug in rslugs:
            tmp = AppInstance.objects.filter(~Q(state="Deleted"), project=project, app__category__slug=rslug['slug']).order_by('-created_on')[:5]
            for instance in tmp:
                pk_list += str(instance.pk)+','
            
            apps = Apps.objects.filter(category__slug=rslug['slug'])
            resources.append({"title": rslug['name'], "objs": tmp, "apps": apps})
        pk_list = pk_list[:-1]
        pk_list = "'"+pk_list+"'"
        models = Model.objects.filter(project=project).order_by('-uploaded_at')[:10]
    
    return render(request, template, locals())


@login_required
def delete(request, user, project_slug):
    next_page = request.GET.get('next', '/projects/')

    owner = User.objects.filter(username=user).first()
    project = Project.objects.filter(owner=owner, slug=project_slug).first()

    print("SCHEDULING DELETION OF ALL INSTALLED APPS")
    from .tasks import delete_project_apps
    delete_project_apps(project_slug)

    print("DELETING KEYCLOAK PROJECT RESOURCES")
    retval = delete_project_resources(project)

    if not retval:
        next_page = request.GET.get('next', '/{}/{}'.format(request.user, project.slug))
        print("could not delete Keycloak resources!")
        return HttpResponseRedirect(next_page, {'message': 'Error during project deletion'})

    print("KEYCLOAK RESOURCES DELETED SUCCESFULLY!")
    

    print("ARCHIVING PROJECT MODELS")
    models = Model.objects.filter(project=project)
    for model in models:
        model.status = 'AR'
        model.save()
    project.status = 'archived'
    project.save()

    return HttpResponseRedirect(next_page, {'message': 'Deleted project successfully.'})


@login_required
def publish_project(request, user, project_slug):
    owner = User.objects.filter(username=user).first()
    project = Project.objects.filter(owner=owner, slug=project_slug).first()

    if request.method == 'POST':
        gh_form = PublishProjectToGitHub(request.POST)

        if gh_form.is_valid():
            user_name = gh_form.cleaned_data['user_name']
            user_password = gh_form.cleaned_data['user_password']

            user_password_bytes = user_password.encode('ascii')
            base64_bytes = base64.b64encode(user_password_bytes)
            user_password_encoded = base64_bytes.decode('ascii')

            url = 'http://{}-file-controller/project/{}/push/{}/{}'.format(
                project_slug, project_slug[:-4], user_name, user_password_encoded)
            try:
                response = r.get(url)

                if response.status_code == 200 or response.status_code == 203:
                    payload = response.json()

                    if payload['status'] == 'OK':
                        clone_url = payload['clone_url']
                        if clone_url:
                            project.clone_url = clone_url
                            project.save()

                            l = ProjectLog(project=project, module='PR', headline='GitHub repository',
                                           description='Published project files to a GitHub repository {url}'.format(
                                               url=project.clone_url))
                            l.save()
            except Exception as e:
                logger.error("Failed to get response from {} with error: {}".format(url, e))

    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project_slug}))


@login_required
def project_readme(request, user, project_slug):
    is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
    
    project = None
    username = request.user.username
    try:
        owner = User.objects.get(username=username)
        project = Project.objects.filter(Q(owner=owner) | Q(authorized=owner), Q(slug=project_slug)).first()
    except Exception as e:
        print('Project not found.')

    readme = None
    if project:     
        url = 'http://{}-file-controller/readme'.format(project.slug)
        try:
            response = r.get(url)
            if response.status_code == 200 or response.status_code == 203:
                payload = response.json()
                if payload['status'] == 'OK':
                    md = markdown.Markdown(extensions=['extra'])
                    readme = md.convert(payload['readme'])
        except Exception as e:
            logger.error("Failed to get response from {} with error: {}".format(url, e))
    
    return render(request, "project_readme.html", locals())
