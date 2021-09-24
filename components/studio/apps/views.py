from django.shortcuts import render, HttpResponseRedirect, reverse, redirect
from django.http import JsonResponse
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q, Subquery
from django.template import engines
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Apps, AppInstance, AppCategories, AppPermission, AppStatus
from projects.models import Project, Flavor, Environment, ReleaseName
from models.models import Model
from projects.helpers import get_minio_keys
import modules.keycloak_lib as keylib
from .serialize import serialize_app
from .tasks import deploy_resource, delete_resource
import requests
import flatten_json
import uuid
import time
from datetime import datetime, timedelta
from .generate_form import generate_form
from .helpers import create_instance_params

def get_status_defs():
    status_success = ['Running', 'Succeeded', 'Success']
    status_warning = ['Pending', 'Installed', 'Waiting', 'Installing', 'Created']
    return status_success, status_warning


# Create your views here.
def index(request, user, project):
    print("hello")
    category = 'store'
    template = 'index_apps.html'
    # status_success = ['Running', 'Succeeded', 'Success']
    # status_warning = ['Pending', 'Installed', 'Waiting', 'Installing']

    # template = 'new.html'
    cat_obj = AppCategories.objects.get(slug=category)
    apps = Apps.objects.filter(category=cat_obj)
    project = Project.objects.get(slug=project)
    appinstances = AppInstance.objects.filter(Q(owner=request.user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True), app__category=cat_obj)

        
    return render(request, template, locals())

def logs(request, user, project, ai_id):
    template = "logs.html"
    app = AppInstance.objects.get(pk=ai_id)
    project = Project.objects.get(slug=project)
    app_settings = app.app.settings
    containers = []
    if 'logs' in app_settings:
        containers = app_settings['logs']
        container = containers[0]
        print("default container: "+container)
        if 'container' in request.GET:
            container = request.GET.get('container')
            print("Got container in request: "+container)
        
        logs = []
        try:
            url = settings.LOKI_SVC+'/loki/api/v1/query_range'
            app_params = app.parameters
            print('{container="'+container+'",release="'+app_params['release']+'"}')
            query = {
            'query': '{container="'+container+'",release="'+app_params['release']+'"}',
            'limit': 50,
            'start': 0,
            }
            res = requests.get(url, params=query)
            res_json = res.json()['data']['result']
            
            for item in res_json:
                logs.append('----------BEGIN CONTAINER------------')
                logline = ''
                for iline in item['values']:
                    logs.append(iline[1])
                logs.append('----------END CONTAINER------------')

        except Exception as e:
            print(e)

    return render(request, template, locals())

def filtered(request, user, project, category):
    # template = 'index_apps.html'
    projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active')
    status_success, status_warning = get_status_defs()
    menu = dict()

    template = 'new.html'
    cat_obj = AppCategories.objects.get(slug=category)
    menu[category] = 'active'
    media_url = settings.MEDIA_URL
    project = Project.objects.get(slug=project)
    try:
        apps = Apps.objects.filter(pk__in=Subquery(
            Apps.objects.filter((Q(access="public") | Q(projects__in=[project])), category=cat_obj).order_by('slug', '-revision').distinct('slug').values('pk')
        )).order_by('-priority')
    except Exception as err:
        print(err)
    
    time_threshold = datetime.now() - timedelta(minutes=5)
    print(time_threshold)
    appinstances = AppInstance.objects.filter(
        Q(owner=request.user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True),
        ~Q(state='Deleted') | Q(deleted_on__gte=time_threshold),
        app__category=cat_obj,
        project=project).order_by('-created_on')
    pk_list = ''
    for instance in appinstances:
        pk_list += str(instance.pk)+','
    pk_list = pk_list[:-1]
    pk_list = "'"+pk_list+"'"
    apps_installed = False
    print("PRINTINGGG: ",appinstances)
    if appinstances:
        apps_installed = True
        
    return render(request, template, locals())

@csrf_exempt
def get_status(request, user, project):
    status_success, status_warning = get_status_defs()
    print("GET_STATUS")
    print(request.POST)
    pk = request.POST.get('pk')
    # print(pk)
    pk = pk.split(',')
    print(pk)
    res = {}
    if len(pk)>0 and not (len(pk)==1 and pk[0]==''):
        appinstances = AppInstance.objects.filter(pk__in=pk)
        print(appinstances)
        res = dict()
        for instance in appinstances:
            try:
                status = instance.status.latest().status_type
                
            except:
                status = instance.state
            if status in status_success:
                span_class = 'bg-success'
            elif status in status_warning:
                span_class = 'bg-warning'
            else:
                span_class = 'bg-danger'
            res['status-{}'.format(instance.pk)] = '<span class="badge {}">{}</span>'.format(span_class, status)
            print(status)
        print(pk)
    return JsonResponse(res)
    # if 'pk' in request.POST:
    #     pk = request.POST['pk']
    #     appinstances = AppInstance.objects.filter(pk__in=pk)
    #     print(appinstances)

def appsettings(request, user, project, ai_id):
    all_tags = AppInstance.tags.tag_model.objects.all()
    template = 'create.html'
    app_action = "Settings"
    if 'from' in request.GET:
        from_page = request.GET.get('from')
    else:
        from_page = 'filtered'

    project = Project.objects.get(slug=project)
    appinstance = AppInstance.objects.get(pk=ai_id)
    existing_app_name = appinstance.name
    app = appinstance.app

    aset = appinstance.app.settings
    form = generate_form(aset, project, app, request.user, appinstance)
    return render(request, template, locals())

def add_releasename(request, user, project, ai_id, rn=None):
    count_rn = ReleaseName.objects.filter(name = request.POST.get('rn')).count()
    available = "false"
    if count_rn == 0:
        available = "true"
        release=ReleaseName()
        release.name = request.POST.get('rn')
        release.status = 'active'
        release.project = Project.objects.get(slug=project)
        release.save()
    print("RELEASE_NAME: ",request.POST.get('rn'),count_rn)
    
    return HttpResponseRedirect(reverse('apps:appsettings', kwargs={'user':user, 'project':project, 'ai_id':ai_id})+"?available="+available+"&rn="+request.POST.get('rn'))

def add_tag(request, user, project, ai_id):
    appinstance = AppInstance.objects.get(pk=ai_id)
    if request.method == 'POST':
        new_tag = request.POST.get('tag', '')
        print("New Tag: ",new_tag)
        appinstance.tags.add(new_tag)
        appinstance.save()

    return HttpResponseRedirect(reverse('apps:appsettings', kwargs={'user':user, 'project':project, 'ai_id':ai_id}))


def remove_tag(request, user, project, ai_id):
    appinstance = AppInstance.objects.get(pk=ai_id)
    if request.method == 'POST':
        print(request.POST)
        new_tag = request.POST.get('tag', '')
        print("Remove Tag: ",new_tag)
        appinstance.tags.remove(new_tag)
        appinstance.save()

    return HttpResponseRedirect(reverse('apps:appsettings', kwargs={'user':user, 'project':project, 'ai_id':ai_id}))

def create(request, user, project, app_slug, data=[], wait=False):
    template = 'create.html'
    app_action = "Create"
    
    if request:
        user = request.user
        if 'from' in request.GET:
            from_page = request.GET.get('from')
        else:
            from_page = 'filtered'
    else:
        from_page = ''
        user = User.objects.get(username=user)


    existing_app_name = ""
    project = Project.objects.get(slug=project)
    app = Apps.objects.filter(slug=app_slug).order_by('-revision')[0]
        

    aset = app.settings

    # Set up form
    print("GENERATING FORM")
    form = generate_form(aset, project, app, user, [])
    print("FORM DONE")
    if data or request.method == "POST":
        if not data:
            data = request.POST
        print("INPUT")
        print(data)
        app_name = data.get('app_name')
        parameters_out, app_deps, model_deps = serialize_app(data, project, aset, user.username)

        if data.get('app_action') == "Create":
            permission = AppPermission(name=app_name)
            permission.save()
        elif data.get('app_action') == "Settings":
            instance = AppInstance.objects.get(pk=data.get('app_id'))
            permission = instance.permission
        else:
            print("No action set, aborting...")
            print(data.get('app_action'))
            return JsonResponse({'status': 'failed', 'reason': 'app_action not set.'})
        permission.public = False
        permission.projects.set([])
        permission.users.set([])
        

        if parameters_out['permissions']['public']:
            permission.public = True
        elif parameters_out['permissions']['project']:
            print("PROJECT PERMISSIONS")
            client_id = project.slug
            kc = keylib.keycloak_init()
            client_secret, res_json = keylib.keycloak_get_client_secret_by_id(kc, client_id)
            if not 'project' in parameters_out:
                parameters_out['project'] = dict()
            parameters_out['project']['client_id'] = client_id
            parameters_out['project']['client_secret'] = client_secret
            parameters_out['project']['slug'] = project.slug
            parameters_out['project']['name'] = project.name
            # parameters_out['project'].update({"client_id": client_id, "client_secret": client_secret})
            print(parameters_out)
            permission.projects.set([project])
        elif parameters_out['permissions']['private']:
            permission.users.set([user])
        permission.save()



        if data.get('app_action') == "Create":
            instance = AppInstance(name=app_name,
                                app=app,
                                project=project,
                                info={},
                                parameters=parameters_out,
                                owner=user)
            
            
            
            create_instance_params(instance, "create")
            
            rel_name_obj = []
            if 'app_release_name' in data and data.get('app_release_name') != '':
                submitted_rn = data.get('app_release_name')
                try:
                    rel_name_obj = ReleaseName.objects.get(name=submitted_rn, project=project, status='active')
                    rel_name_obj.status = 'in-use'
                    rel_name_obj.save()
                    instance.parameters['release'] = submitted_rn
                except Exception as e:
                    print("Error: Submitted release name is not owned by project.")
                    print(e)
                    return HttpResponseRedirect(
                        reverse('projects:details', kwargs={'user': request.user, 'project_slug': str(project.slug)}))
                
                

            # Add field for table.    
            if instance.app.table_field and instance.app.table_field != "":
                django_engine = engines['django']
                info_field = django_engine.from_string(instance.app.table_field).render(instance.parameters)
                instance.table_field = eval(info_field)
            else:
                instance.table_field = {}


            # instance.state = "Waiting"
            status = AppStatus(appinstance=instance)
            status.status_type = 'Created'
            status.info = instance.parameters['release']
            instance.save()
            if rel_name_obj:
                rel_name_obj.app = instance
                rel_name_obj.save()
            status.save()
            
            
            permission.appinstance = instance
            permission.save()
            instance.app_dependencies.set(app_deps)
            instance.model_dependencies.set(model_deps)

            # Setting up Keycloak and deploying resources.
            res = deploy_resource.delay(instance.pk, "create")
            if wait:
                while not res.ready():
                    time.sleep(0.1)

        elif data.get('app_action') == "Settings":
            print("UPDATING APP DEPLOYMENT")
            print(instance)
            instance.name = app_name
            instance.parameters.update(parameters_out)
            instance.save()
            instance.app_dependencies.set(app_deps)
            instance.model_dependencies.set(model_deps)

            res = deploy_resource.delay(instance.pk, "update")
        else:
            raise Exception("Incorrect action on app.")
        
        if request:
            if 'from' in request.GET:
                from_page = request.GET.get('from')
                if from_page == "overview":
                    return HttpResponseRedirect(
                        reverse('projects:details', kwargs={'user': request.user, 'project_slug': str(project.slug)}))
                elif from_page == "filtered":
                    return HttpResponseRedirect(
                        reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project.slug), 'category': instance.app.category.slug}))
            else:
                return HttpResponseRedirect(
                        reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project.slug), 'category': instance.app.category.slug}))
        else:
            return JsonResponse({"status": "ok"})
    return render(request, template, locals())

def publish(request, user, project, category, ai_id):
    print("Publish app {}".format(ai_id))
    print(project)
    try:
        app = AppInstance.objects.get(pk=ai_id)
        print(app)
        # TODO: Check that user is allowed to publish this app.
        print("setting public")
        if app.access == "private":
            app.access = "public"
        else:
            app.access = "private"
        print("saving")
        app.save()
        print("done")
    except Exception as err:
        print(err)

    return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))


def delete(request, user, project, category, ai_id):
    print("PK="+str(ai_id))

    if 'from' in request.GET:
        from_page = request.GET.get('from')
    else:
        from_page = 'filtered'

    delete_resource.delay(ai_id)        

    if 'from' in request.GET:
        from_page = request.GET.get('from')
        if from_page == "overview":
            return HttpResponseRedirect(
                reverse('projects:details', kwargs={'user': request.user, 'project_slug': str(project)}))
        elif from_page == "filtered":
            return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))
        else:
            return HttpResponseRedirect(
                    reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))

    return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))