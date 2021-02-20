from django.shortcuts import render, HttpResponseRedirect, reverse
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q
from django.template import engines
from .models import Apps, AppInstance, AppCategories, AppPermission
from projects.models import Project, Volume, Flavor, Environment
from models.models import Model
from projects.helpers import get_minio_keys
import modules.keycloak_lib as keylib
from .serialize import serialize_app
from .tasks import deploy_resource, delete_resource
import requests
import flatten_json
import uuid


key_words = ['appobj', 'model', 'flavor', 'environment', 'volumes', 'apps', 'logs', 'permissions', 'csrfmiddlewaretoken']

# Create your views here.
def index(request, user, project):
    template = 'index_apps.html'
    apps = Apps.objects.all()
    project = Project.objects.get(slug=project)

    appinstances = AppInstance.objects.filter(owner=request.user)
    apps_installed = False
    if appinstances:
        apps_installed = True
        
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
    template = 'index_apps.html'
    cat_obj = AppCategories.objects.get(slug=category)
    apps = Apps.objects.filter(category=cat_obj)
    project = Project.objects.get(slug=project)
    appinstances = AppInstance.objects.filter(Q(owner=request.user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True), app__category=cat_obj)

    apps_installed = False
    if appinstances:
        apps_installed = True
        
    return render(request, template, locals())


def get_form_models(aset, project, appinstance=[]):
    dep_model = False
    models = []
    if 'model' in aset:
        print('app requires a model')
        dep_model = True
        models = Model.objects.filter(project=project)
        
        for model in models:
            if appinstance and model.appinstance_set.filter(pk=appinstance.pk).exists():
                print(model)
                model.selected = "selected"
            else:
                model.selected = ""
    return dep_model, models

def get_form_apps(aset, project, myapp, user, appinstance=[]):
    dep_apps = False
    app_deps = []
    if 'apps' in aset:
        dep_apps = True
        app_deps = dict()
        apps = aset['apps']
        for app_name, option_type in apps.items():
            print(app_name)
            app_obj = Apps.objects.get(name=app_name)

            # TODO: Only get app instances that we have permission to list.
            app_instances = AppInstance.objects.filter(Q(owner=user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True), project=project, app=app_obj)
            # TODO: Special case here for "environment" app. Maybe fix, or maybe OK.
            # Could be solved by supporting "condition": '"appobj.app_slug":"true"'
            if app_name == "Environment":
                key = 'appobj'+'.'+myapp.slug

                app_instances = AppInstance.objects.filter(Q(owner=user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True),
                                                           project=project,
                                                           app=app_obj,
                                                           parameters__contains={
                                                               "appobj": {
                                                                    myapp.slug: True
                                                                }
                                                           })
            
            for ain in app_instances:
                if appinstance and ain.appinstance_set.filter(pk=appinstance.pk).exists():
                    ain.selected = "selected"
                else:
                    ain.selected = ""

            if option_type == "one":
                app_deps[app_name] = {"instances": app_instances, "option_type": ""}
            else:
                app_deps[app_name] = {"instances": app_instances, "option_type": "multiple"}
    return dep_apps, app_deps

def get_form_primitives(aset, project, appinstance=[]):
    all_keys = aset.keys()
    print("PRIMITIVES")
    primitives = dict()
    if appinstance:
        ai_vals = flatten_json.flatten(appinstance.parameters, '.')
    for key in all_keys:
        if key not in key_words:
            primitives[key] = aset[key]
            if appinstance:
                for subkey, subval in aset[key].items():
                    primitives[key][subkey]['default'] = ai_vals[key+'.'+subkey]
    print(primitives)
    return primitives

def get_form_permission(aset, project, appinstance=[]):
    form_permissions = {
        "public": {"value":"false", "option": "false"},
        "project": {"value":"false", "option": "false"},
        "private": {"value":"true", "option": "true"}
    }
    dep_permissions = True
    if 'permissions' in aset:
        form_permissions = aset['permissions']
        # if not form_permissions:
        #     dep_permissions = False

        if appinstance:
            try:
                ai_vals = eval(appinstance.parameters)
                form_permissions['public']['value'] = ai_vals['permissions.public']
                form_permissions['project']['value'] = ai_vals['permissions.project']
                form_permissions['private']['value'] = ai_vals['permissions.private']
            except:
                print("Permissions not set for app instance, using default.")
    return dep_permissions, form_permissions

def get_form_appobj(aset, project, appinstance=[]):
    print("CHECKING APP OBJ")
    dep_appobj = False
    appobjs = dict()
    if 'appobj' in aset:
        print("NEEDS APP OBJ")
        dep_appobj = True
        appobjs['objs'] = Apps.objects.all()
        appobjs['title'] = aset['appobj']['title']
        appobjs['type'] = aset['appobj']['type']

    print(appobjs)
    return dep_appobj, appobjs


def appsettings(request, user, project, ai_id):
    template = 'create.html'
    app_action = "Settings"

    project = Project.objects.get(slug=project)
    appinstance = AppInstance.objects.get(pk=ai_id)
    existing_app_name = appinstance.name
    app = appinstance.app

    aset = appinstance.app.settings
    # get_form_models(aset, project, appinstance=appinstance)
    dep_apps, app_deps = get_form_apps(aset, project, app, request.user, appinstance=appinstance)
    dep_model, models = get_form_models(aset, project, appinstance=appinstance)
    primitives = get_form_primitives(aset, project, appinstance=appinstance)
    dep_permissions, form_permissions = get_form_permission(aset, project, appinstance=appinstance)

    return render(request, template, locals())



def create_instance_params(instance, action="create"):
    # instance_settings = eval(instance.settings)
    if action == "create":
        RELEASE_NAME = instance.app.slug.replace('_', '-')+'-'+instance.project.slug+'-'+uuid.uuid4().hex[0:4]
        print("RELEASE_NAME: "+RELEASE_NAME)
    else:
        print(instance.parameters)
        RELEASE_NAME = instance.parameters['release']


    SERVICE_NAME = RELEASE_NAME
    # TODO: Fix for multicluster setup, look at e.g. labs
    HOST = settings.DOMAIN
    NAMESPACE = settings.NAMESPACE

    user = instance.owner

    skip_tls = 0
    if not settings.OIDC_VERIFY_SSL:
        skip_tls = 1
        print("WARNING: Skipping TLS verify.")

    # Add some generic parameters.
    parameters = {
        "release": RELEASE_NAME,
        "chart": str(instance.app.chart),
        "namespace": NAMESPACE,
        "appname": RELEASE_NAME,
        "project": {
            "name": instance.project.name,
            "slug": instance.project.slug
        },
        "global": {
            "domain": HOST,
        },
        "s3sync": {
            "image": "scaleoutsystems/s3-sync:latest"
        },
        "gatekeeper": {
            "skip_tls": str(skip_tls)
        },
        "service": {
            "name": SERVICE_NAME
        },
        "storageClass": settings.STORAGECLASS
    }

    instance.parameters.update(parameters)


    # Add field for table.    
    if instance.app.table_field and instance.app.table_field != "":
        django_engine = engines['django']
        info_field = django_engine.from_string(instance.app.table_field).render(parameters)
        instance.table_field = info_field
    else:
        instance.table_field = ""

def create(request, user, project, app_slug):
    template = 'create.html'
    app_action = "Create"



    existing_app_name = ""
    project = Project.objects.get(slug=project)
    app = Apps.objects.get(slug=app_slug)

    aset = app.settings

    # Set up form
    dep_model, models = get_form_models(aset, project, [])
    dep_apps, app_deps = get_form_apps(aset, project, app, request.user, [])
    dep_appobj, appobjs = get_form_appobj(aset, project, [])

    dep_vols = False
    dep_flavor = False
    if 'flavor' in aset:
        dep_flavor = True
        flavors = Flavor.objects.all()
    
    dep_environment = False
    if 'environment' in aset:
        dep_environment = True
        environments = Environment.objects.all()


    primitives = get_form_primitives(aset, project, [])
    dep_permissions, form_permissions = get_form_permission(aset, project, [])

    print("::::::::::::")





    if request.method == "POST":
        app_name = request.POST.get('app_name')
        parameters_out, app_deps, model_deps = serialize_app(request.POST)

        if request.POST.get('app_action') == "Create":
            permission = AppPermission(name=app_name)
            permission.save()
        elif request.POST.get('app_action') == "Settings":
            instance = AppInstance.objects.get(pk=request.POST.get('app_id'))
            permission = instance.permission

        permission.public = False
        permission.projects.set([])
        permission.users.set([])
        

        if parameters_out['permissions']['public']:
            permission.public = True
        elif parameters_out['permissions']['project']:

            client_id = project.slug
            kc = keylib.keycloak_init()
            client_secret = keylib.keycloak_get_client_secret_by_id(kc, client_id)
            if not 'project' in parameters_out:
                parameters_out['project'] = dict()
            parameters_out['project'].update({"client_id": client_id, "client_secret": client_secret})
            permission.projects.set([project])
        elif parameters_out['permissions']['private']:
            permission.users.set([request.user])
        permission.save()



        if request.POST.get('app_action') == "Create":
            instance = AppInstance(name=app_name,
                                app=app,
                                project=project,
                                settings=str(request.POST.dict()),
                                parameters=parameters_out,
                                owner=request.user)
            create_instance_params(instance, "create")
            instance.save()
            permission.appinstance = instance
            permission.save()
            instance.app_dependencies.set(app_deps)
            instance.model_dependencies.set(model_deps)
            
            deploy_resource.delay(instance.pk, "create")

        elif request.POST.get('app_action') == "Settings":
            print("UPDATING APP DEPLOYMENT")
            print(instance)
            instance.name = app_name
            instance.settings = str(request.POST.dict())
            instance.parameters.update(parameters_out)
            create_instance_params(instance, "update")
            instance.save()
            instance.app_dependencies.set(app_deps)
            instance.model_dependencies.set(model_deps)

            deploy_resource.delay(instance.pk, "update")
        else:
            raise Exception("Incorrect action on app.")

        return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project.slug), 'category': instance.app.category.slug}))

    return render(request, template, locals())

def delete(request, user, project, category, ai_id):
    print("PK="+str(ai_id))

    # Check that the app instance actually exists.
    appinstance = []
    try:
        appinstance = AppInstance.objects.get(pk=ai_id)
    except:
        print("WARN: AppInstance doesn't exist.")

    
    if appinstance:
        # The instance does exist.
        # TODO: Check that the user has the permission required to delete it.

        # Clean up in Keycloak.
        kc = keylib.keycloak_init()
        # TODO: Fix for multicluster setup
        # TODO: We are assuming this URI here, but we should allow for other forms.
        # The instance should store information about this.
        URI =  'https://'+appinstance.parameters['release']+'.'+settings.DOMAIN
        
        keylib.keycloak_remove_client_valid_redirect(kc, appinstance.project.slug, URI.strip('/')+'/*')
        keylib.keycloak_delete_client(kc, appinstance.parameters['gatekeeper']['client_id']) 
        scope_id = keylib.keycloak_get_client_scope_id(kc, appinstance.parameters['gatekeeper']['client_id']+'-scope')
        keylib.keycloak_delete_client_scope(kc, scope_id)
        
        # Delete installed resources on the cluster.
        release = appinstance.parameters['release']
        namespace = appinstance.parameters['namespace']
        delete_resource.delay({"release": release, "namespace": namespace})

        # Delete the instance
        # appinstance.permission.delete()
        appinstance.delete()

        print("BOTTOM")
    
        

    return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))