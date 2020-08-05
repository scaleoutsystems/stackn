from django.shortcuts import render, HttpResponseRedirect, reverse
from projects.models import Project
from .models import Session
from projects.models import Environment, Flavor
from django.contrib.auth.decorators import login_required
import uuid
from django.conf import settings
from django.db.models import Q
from projects.helpers import get_minio_keys


@login_required(login_url='/accounts/login')
def index(request, user, project):
    template = 'labs/index.html'
    project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first()
    sessions = Session.objects.filter(project=project)
    flavors = Flavor.objects.all()
    environments = Environment.objects.all()
    url = settings.DOMAIN

    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def run(request, user, project):
    project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first()

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

        print("dispatching with {}  {}".format(flavor, name))
        import base64
        if name != '' and flavor is not None:
            # Default values here, because otherwise an old deployment can stop working
            # if the deployment configuration files are not compatible with the latest
            # studio image.
            ingress_secret_name = 'prod-ingress'
            try:
                ingress_secret_name = settings.LABS['ingress']['secretName']
            except:
                pass

            minio_keys = get_minio_keys(project)
            decrypted_key = minio_keys['project_key']
            decrypted_secret = minio_keys['project_secret']

            prefs = {'labs.resources.requests.cpu': str(flavor.cpu),
                     'labs.resources.limits.cpu': str(flavor.cpu),
                     'labs.resources.requests.memory': str(flavor.mem),
                     'labs.resources.limits.memory': str(flavor.mem),
                     'labs.resources.requests.gpu': str(flavor.gpu),
                     'labs.resources.limits.gpu': str(flavor.gpu),
                     'labs.gpu.enabled': str("true" if flavor.gpu else "false"),
                     'labs.image': environment.image,
                     'ingress.secretName': ingress_secret_name,
                     # 'labs.setup': environment.setup,
                     'minio.access_key': decrypted_key,
                     'minio.secret_key': decrypted_secret,
                     }
            session = Session.objects.create_session(name=name, project=project, chart='lab', settings=prefs)
            from .helpers import create_session_resources

            print("trying to create resources")
            retval = create_session_resources(request, user, session, prefs, project)
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
    project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first()
    session = Session.objects.filter(id=id, project=project).first()

    if session:
        from .helpers import delete_session_resources
        delete_session_resources(session)
        session.delete()

    return HttpResponseRedirect(
        reverse('labs:index', kwargs={'user': request.user, 'project': str(project.slug)}))
