from django.shortcuts import render, HttpResponseRedirect, reverse
from projects.models import Project
from .models import Session
from projects.models import Environment
from django.contrib.auth.decorators import login_required
import uuid
from django.conf import settings


@login_required(login_url='/accounts/login')
def index(request, user, project):
    template = 'labs/index.html'
    project = Project.objects.filter(slug=project, owner=request.user).first()
    sessions = Session.objects.filter(project=project)
    environments = Environment.objects.filter(project=project)
    url = settings.DOMAIN

    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def run(request, user, project):
    template = 'labs/index.html'
    project = Project.objects.filter(slug=project, owner=request.user).first()

    if request.method == "POST":
        uid = uuid.uuid4()
        name = str(project.slug) + str(uid)[0:7]
        cpu = request.POST.get('cpu', '')
        cpu = '' + cpu + ''
        memory = request.POST.get('memory', '')
        memory = '' + memory + 'Gi'
        gpu = request.POST.get('gpu','')
        if gpu == '0':
            gpu = ''
        #repository = request.POST.get('repository', '')
        repository = ''
        if not project.repository_imported:
            repository = project.repository
            project.repository_imported = True
        image = request.POST.get('image', '')
        print("dispatching with {}  and cpu {} and memory {}".format(name, cpu, memory))
        if name != '' and cpu != '' and memory != '':
            from .models import SessionManager
            prefs = {'labs.requests.memory': memory,
                     'labs.limits.memory': memory,
                     'labs.requests.cpu': cpu,
                     'labs.limits.cpu': cpu,
                     'labs.gpu': gpu ,
                     'labs.limits.gpu': gpu,
                     'labs.repository': str(repository),
                     'labs.image': image,
                     'minio.access_key': project.project_key,
                     'minio.secret_key': project.project_secret,
                     }
            session = Session.objects.create_session(name=name, project=project, chart='lab', settings=prefs)
            from .helpers import create_session_resources

            print("trying to create resources")
            retval = create_session_resources(session, prefs, project, repository=repository)
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
    session = Session.objects.filter(id=id,project=project).first()

    if session:
        from .helpers import delete_session_resources
        delete_session_resources(session)
        session.delete()

    return HttpResponseRedirect(
        reverse('labs:index', kwargs={'user': request.user, 'project': str(project.slug)}))
