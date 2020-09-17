from django.shortcuts import render, reverse
from .models import Project, Environment, ProjectLog
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
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
import modules.keycloak_lib as kc
from datetime import datetime, timedelta
from modules.project_auth import get_permissions
from .helpers import create_project_resources


logger = logging.getLogger(__name__)


def index(request):
    template = 'index_projects.html'
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user)).distinct('pk')
    except TypeError as err:
        projects = []
        print(err)

    request.session['next'] = '/projects/'
    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def settings(request, user, project_slug):
    user_permissions = get_permissions(request, project_slug, sett.PROJECT_SETTINGS_PERM)
    print(user_permissions)
    template = 'settings.html'
    project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), Q(slug=project_slug)).first()
    url_domain = sett.DOMAIN
    platform_users = User.objects.filter(~Q(pk=project.owner.pk))
    environments = Environment.objects.all()

    minio_keys = get_minio_keys(project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']

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

@login_required(login_url='/accounts/login')
def download_settings(request, user, project_slug):
    # Get user token
    from rest_framework.authtoken.models import Token
    token = Token.objects.get_or_create(user=request.user)
    project_instance = Project.objects.get(slug=project_slug)
    proj_settings = "Dummy"
    # proj_settings = create_settings_file(project_instance, user, token[0].key)
    response = HttpResponse(proj_settings, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename={0}'.format('project.yaml')
    return response


@login_required(login_url='/accounts/login')
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


@login_required(login_url='/accounts/login')
def grant_access_to_project(request, user, project_slug):
    project = Project.objects.filter(slug=project_slug).first()

    if request.method == 'POST':

        print(request.POST)
        # if form.is_valid():
        # print('Form valid:')
        # print(form.is_valid())

        selected_users = request.POST.getlist('selected_users') #form.cleaned_data.get('selected_users')
        print('Selected users:')
        print(request.POST.getlist('selected_users'))
        print('....')
        project.authorized.set(selected_users)
        project.save()

        l = ProjectLog(project=project, module='PR', headline='New members',
                       description='{number} new members have been added to the Project'.format(
                           number=len(selected_users)))
        l.save()

        if len(selected_users) == 1:
            selected_users = list(selected_users)

        for selected_user in selected_users:
            user_tmp = User.objects.get(pk=selected_user)
            username_tmp = user_tmp.username
            logger.info('Trying to add user {} to project.'.format(username_tmp))
            kc.keycloak_add_role_to_user(project.slug, username_tmp, 'member')

    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': user, 'project_slug': project.slug}))

@login_required(login_url='/accounts/login')
def create(request):
    template = 'index_projects.html'

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
            # Create project resources
            create_project_resources(project, request.user.username, repository)
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


@login_required(login_url='/accounts/login')
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
        message = 'No project found'

    filename = None
    readme = None
    url = 'http://{}-file-controller/readme'.format(project.slug)
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

    project_logs = ProjectLog.objects.filter(project=project).order_by('-created_at')

    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def delete(request, user, project_slug):
    next_page = request.GET.get('next', '/projects/')

    owner = User.objects.filter(username=user).first()
    project = Project.objects.filter(owner=owner, slug=project_slug).first()

    retval = delete_project_resources(project)

    if not retval:
        next_page = request.GET.get('next', '/{}/{}'.format(request.user, project.slug))
        print("could not delete!")
        return HttpResponseRedirect(next_page, {'message': 'Error during project deletion'})

    print("PROJECT RESOURCES DELETED SUCCESFULLY!")

    models = Model.objects.filter(project=project)
    for model in models:
        model.status = 'AR'
        model.save()
    project.delete()

    return HttpResponseRedirect(next_page, {'message': 'Deleted project successfully.'})


@login_required(login_url='/accounts/login')
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


@login_required(login_url='/accounts/login')
def load_project_activity(request, user, project_slug):
    template = 'project_activity.html'

    time_period = request.GET.get('period')
    if time_period == 'week':
        last_week = datetime.today() - timedelta(days=7)
        project_logs = ProjectLog.objects.filter(created_at__gte=last_week).order_by('-created_at')
    elif time_period == 'month':
        last_month = datetime.today() - timedelta(days=30)
        project_logs = ProjectLog.objects.filter(created_at__gte=last_month).order_by('-created_at')
    else:
        project_logs = ProjectLog.objects.all().order_by('-created_at')

    return render(request, template, {'project_logs': project_logs})


