from django.shortcuts import render, reverse
from .models import Project, Environment
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from .exceptions import ProjectCreationException
from .helpers import create_project_resources, delete_project_resources, create_settings_file
from django.contrib.auth.models import User
from django.conf import settings as sett
import logging
import markdown
from .forms import TransferProjectOwnershipForm
from django.db.models import Q

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
    template = 'settings.html'
    project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), Q(slug=project_slug)).first()
    url_domain = sett.DOMAIN
    platform_users = User.objects.filter(~Q(pk=project.owner.pk))
    environments = Environment.objects.all()

    if request.method == 'POST':
        form = TransferProjectOwnershipForm(request.POST)
        if form.is_valid():
            new_owner_id = int(form.cleaned_data['transfer_to'])
            new_owner = User.objects.filter(pk=new_owner_id).first()
            project.owner = new_owner
            project.save()
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
    proj_settings = create_settings_file(project_instance, user, token[0].key)
    response = HttpResponse(proj_settings, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename={0}'.format('project.yaml')
    return response

@login_required(login_url='/accounts/login')
def change_environment(request, user, project_slug):
    project = Project.objects.filter(slug=project_slug).first()
    environment = project.environment
    from .models import Environment

    if request.method == 'POST':
        environment_slug = request.POST.get('environment', '')
        if environment_slug is not '':
            environment = Environment.objects.filter(slug=environment_slug).first()
            if environment:
                project.environment = environment
                project.save()
        # TODO fix the create_environment_image creation
        #from .helpers import create_environment_image
        #create_environment_image(project)
    return HttpResponseRedirect(
        reverse('projects:settings', kwargs={'user': request.user, 'project_slug': project.slug}))


@login_required(login_url='/accounts/login')
def create(request):
    template = 'index_projects.html'

    if request.method == 'POST':
        name = request.POST.get('name', 'default')
        access = request.POST.get('access', 'org')
        description = request.POST.get('description', '')
        repository = request.POST.get('repository', '')
        project = Project.objects.create_project(name=name, owner=request.user, description=description,
                                                 repository=repository)

        success = True
        try:
            create_project_resources(project, request.user, repository=repository)
        except ProjectCreationException as e:
            print("ERROR: could not create project resources")
            success = False

        if success:
            project.save()

        next_page = request.POST.get('next', '/{}/{}'.format(request.user, project.slug))

        return HttpResponseRedirect(next_page, {'message': 'Created project'})

    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def details(request, user, project_slug):
    template = 'project.html'

    url_domain = sett.DOMAIN

    project = None
    message = None

    try:
        owner = User.objects.filter(username=user).first()
        project = Project.objects.filter(Q(owner=owner) | Q(authorized=owner), Q(slug=project_slug)).first()
    except Exception as e:
        message = 'No project found'

    filename = None
    readme = None
    import requests as r
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

    project.delete()

    return HttpResponseRedirect(next_page, {'message': 'Deleted project successfully.'})


def auth(request):
    if request.user.is_authenticated:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=403)
