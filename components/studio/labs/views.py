from django.shortcuts import render, HttpResponseRedirect, reverse
from projects.models import Project
from .models import Session
from projects.models import Environment, Flavor
from django.contrib.auth.decorators import login_required
import uuid
from django.conf import settings


@login_required(login_url='/accounts/login')
def index(request, user, project):
    template = 'labs/index.html'
    project = Project.objects.filter(slug=project, owner=request.user).first()
    sessions = Session.objects.filter(project=project)
    flavors = Flavor.objects.all()
    environments = Environment.objects.filter(project=project)
    url = settings.DOMAIN

    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def run(request, user, project):

    project = Project.objects.filter(slug=project, owner=request.user).first()

    if request.method == "POST":
        uid = uuid.uuid4()
        name = str(project.slug) + str(uid)[0:7]
        flavor_slug = request.POST.get('flavor', None)
        environment_slug = request.POST.get('environment', None)

        if flavor_slug:
            flavor = Flavor.objects.filter(slug=flavor_slug).first()
        else:
            flavor = Flavor.objects.all().first()

        if environment_slug:
            environment = Environment.objects.filter(slug=environment_slug).first()
        else:
            environment = Environment.objects.filter.all().first()

        print("dispatching with {}  ".format(flavor, name))
        if name != '' and flavor is not None:
            prefs = {'labs.resources': flavor.resources,
                     'labs.selectors': flavor.selectors,
                     'labs.image': environment.image,
                     #'labs.setup': environment.setup,
                     'minio.access_key': project.project_key,
                     'minio.secret_key': project.project_secret,
                     }
            session = Session.objects.create_session(name=name, project=project, chart='lab', settings=prefs)
            from .helpers import create_session_resources

            print("trying to create resources")
            retval = create_session_resources(session, prefs, project)
            if retval:
                print("saving session!")
                project.save()
                session.save()
                return HttpResponseRedirect(
                    reverse('labs:index', kwargs={'user': request.user, 'project': str(project.slug)}))

    return HttpResponseRedirect(
        reverse('labs:index', kwargs={'user': request.user, 'project': str(project.slug)}))


@login_required(login_url='/accounts/login')
def delete(request, user, project, id):
    template = 'labs/index.html'
    project = Project.objects.filter(slug=project, owner=request.user).first()
    session = Session.objects.filter(id=id, project=project).first()

    if session:
        from .helpers import delete_session_resources
        delete_session_resources(session)
        session.delete()

    return HttpResponseRedirect(
        reverse('labs:index', kwargs={'user': request.user, 'project': str(project.slug)}))
