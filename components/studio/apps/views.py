from django.shortcuts import render, HttpResponseRedirect, reverse
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q
from .models import Apps, AppInstance, AppCategories, AppPermission
from projects.models import Project, Volume, Flavor, Environment
from models.models import Model
from projects.helpers import get_minio_keys
import modules.keycloak_lib as keylib
import requests
import flatten_json


key_words = ['model', 'flavor', 'environment', 'volumes', 'apps', 'logs', 'permissions', 'csrfmiddlewaretoken']

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
    app_settings = eval(app.app.settings)
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
            app_params = eval(app.helmchart.params)
            print('{container="'+container+'",app="'+app_params['release']+'"}')
            query = {
            'query': '{container="'+container+'",app="'+app_params['release']+'"}',
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

def serialize_model(form_selection):
    print("SERIALIZING MODEL")
    model_json = dict()
    obj = []
    if 'model' in form_selection:
        model_id = form_selection.get('model', None)
        obj = Model.objects.filter(pk=model_id)
        print("Fetching selected model:")

        
        # model_json['model'] = dict()
        model_json['model.name'] = obj[0].name
        model_json['model.version'] = obj[0].version
        model_json['model.release_type'] = obj[0].release_type
        model_json['model.description'] = obj[0].description
        # TODO: Fix for multicluster setup
        model_json['model.url'] = "https://minio-"+obj[0].project.slug+'.'+settings.DOMAIN
        keys = get_minio_keys(obj[0].project)
        model_json['model.access_key'] = keys['project_key']
        model_json['model.secret_key'] = keys['project_secret']
        model_json['model.bucket'] = 'models'
        model_json['model.obj'] = obj[0].uid
    return model_json, obj

def serialize_flavor(form_selection):
    print("SERIALIZING FLAVOR")
    flavor_json = dict()
    if 'flavor' in form_selection:
        flavor_id = form_selection.get('flavor', None)
        flavor = Flavor.objects.get(pk=flavor_id)
        flavor_json['flavor.requests.memory'] = flavor.mem
        flavor_json['flavor.requests.cpu'] = flavor.cpu
        flavor_json['flavor.limits.memory'] = flavor.mem
        flavor_json['flavor.limits.cpu'] = flavor.cpu
        flavor_json['flavor.gpu.enabled'] = "false"
        if flavor.gpu and flavor.gpu > 0:
            flavor_json['flavor.gpu'] = flavor.gpu
            flavor_json['flavor.gpu.enabled'] = "true"
    return flavor_json

def serialize_environment(form_selection):
    print("SERIALIZING ENVIRONMENT")
    environment_json = dict()
    if 'environment' in form_selection:
        environment_id = form_selection.get('environment', None)
        environment = Environment.objects.get(pk=environment_id)
        environment_json['environment.image'] = environment.image

    return environment_json


def serialize_apps(form_selection):
    print("SERIALIZING DEPENDENT APPS")
    parameters = dict()
    parameters['apps'] = dict()
    app_deps = []
    for key in form_selection.keys():
        if "app:" in key and key[0:4] == "app:":
            
            app_name = key[4:]
            app = Apps.objects.get(name=app_name)
            parameters['apps'][app.slug] = dict()
            print(app_name)
            print('id: '+str(form_selection[key]))
            objs = AppInstance.objects.filter(pk__in=form_selection.getlist(key))

            for obj in objs:
                app_deps.append(obj)
                parameters['apps'][app.slug][slugify(obj.name)] = eval(obj.helmchart.params)
    print("APP PARAMS:")
    print(flatten_json.flatten(parameters, '.'))
    return flatten_json.flatten(parameters, '.'), app_deps

## SERIALIZE VOLUMES
def make_volume_param(vols):
    
    parameters = dict()
    
    parameters['volumes'] = dict()
    for volobject in vols:
        if volobject:
            print(volobject)
            parameters['volumes'][volobject.name] = dict()
            parameters['volumes'][volobject.name]['name'] = volobject.name
            parameters['volumes'][volobject.name]['claim'] = volobject.slug
    print(flatten_json.flatten(parameters, '.'))
    return flatten_json.flatten(parameters, '.')

        
    return volume_param

def serialize_volumes(form_selection):
    print("SERIALIZING VOLUMES")
    parameters = dict()
    volumes = []
    if 'volumes' in form_selection:
        print("VOLUMES PRESENT")
        vol_ids = form_selection.getlist('volumes', None)
        volumes = Volume.objects.filter(pk__in=vol_ids)
        if not volumes:
            volumes = Volume.objects.filter(pk=vol_ids)
        print(volumes)
        parameters = make_volume_param(volumes)
    print(parameters)
    return parameters, volumes
## ------------------------------------------

def serialize_primitives(form_selection):
    print("SERIALIZING PRIMITIVES")
    parameters = dict()
    keys = form_selection.keys()
    for key in keys:
        if key not in key_words and 'app:' not in key:
            parameters[key] = form_selection[key]
    print(parameters)
    return parameters

def serialize_permissions(form_selection):
    print("SERIALIZING PERMISSIONS")
    parameters = dict()
    parameters = {
        "permissions.public": "false",
        "permissions.project": "false",
        "permissions.private": "false"
    }
    permission = form_selection.get('permission', None)
    parameters['permissions.'+permission] = "true"
    print(parameters)
    return parameters

def serialize_app(form_selection):
    print("SERIALIZING APP")
    parameters = dict()

    model_params, model_deps = serialize_model(form_selection)
    parameters.update(model_params)

    app_params, app_deps = serialize_apps(form_selection)
    parameters.update(app_params)

    vol_params, vol_deps = serialize_volumes(form_selection)
    parameters.update(vol_params)

    prim_params = serialize_primitives(form_selection)
    parameters.update(prim_params)

    flavor_params = serialize_flavor(form_selection)
    parameters.update(flavor_params)

    environment_params = serialize_environment(form_selection)
    parameters.update(environment_params)

    permission_params = serialize_permissions(form_selection)
    parameters.update(permission_params)

    return parameters, app_deps, vol_deps, model_deps

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

def get_form_apps(aset, project, appinstance=[]):
    dep_apps = False
    app_deps = []
    if 'apps' in aset:
        dep_apps = True
        app_deps = dict()
        apps = aset['apps']
        for app_name, option_type in apps.items():
            print(app_name)
            app_obj = Apps.objects.get(name=app_name)
            app_instances = AppInstance.objects.filter(project=project, app=app_obj)
            
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
        ai_vals = eval(appinstance.parameters)
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


def appsettings(request, user, project, ai_id):
    template = 'create.html'
    app_action = "Settings"

    project = Project.objects.get(slug=project)
    appinstance = AppInstance.objects.get(pk=ai_id)
    existing_app_name = appinstance.name
    app = appinstance.app

    aset = eval(appinstance.app.settings)
    # get_form_models(aset, project, appinstance=appinstance)
    dep_apps, app_deps = get_form_apps(aset, project, appinstance=appinstance)
    dep_model, models = get_form_models(aset, project, appinstance=appinstance)
    primitives = get_form_primitives(aset, project, appinstance=appinstance)
    dep_permissions, form_permissions = get_form_permission(aset, project, appinstance=appinstance)

    return render(request, template, locals())


def create(request, user, project, app_slug):
    template = 'create.html'
    app_action = "Create"



    existing_app_name = ""
    project = Project.objects.get(slug=project)
    app = Apps.objects.get(slug=app_slug)

    aset = eval(app.settings)

    # Set up form

    dep_model, models = get_form_models(aset, project, [])

    dep_apps, app_deps = get_form_apps(aset, project, [])


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
        print(request.POST)
        app_name = request.POST.get('app_name')
        parameters_out, app_deps, vol_deps, model_deps = serialize_app(request.POST)
        print("PARAMETERS OUT")
        print(parameters_out)
        print(".............")
        print(request.POST.dict())


        if request.POST.get('app_action') == "Create":
            permission = AppPermission(name=app_name)
            permission.save()
        elif request.POST.get('app_action') == "Settings":
            instance = AppInstance.objects.get(pk=request.POST.get('app_id'))
            permission = instance.permission

        if parameters_out['permissions.public'] == "true":
            permission.public = True
        elif parameters_out['permissions.project'] == "true":
            client_id = project.slug
            parameters_out['project.client_id'] = client_id
            kc = keylib.keycloak_init()
            client_secret = keylib.keycloak_get_client_secret_by_id(kc, client_id)
            print(client_id)
            print(client_secret)

            parameters_out['project.client_secret'] = client_secret
            permission.projects.set([project])
        elif parameters_out['permissions.private'] == "true":
            permission.users.set([request.user])
        permission.save()

        if request.POST.get('app_action') == "Create":
            
            
            
            
            print(permission)
            instance = AppInstance(name=app_name,
                                app=app,
                                permission=permission,
                                project=project,
                                settings=str(request.POST.dict()),
                                parameters=str(parameters_out),
                                owner=request.user)
            instance.action = "create"
            instance.save()
            instance.app_dependencies.set(app_deps)
            instance.vol_dependencies.set(vol_deps)
            instance.model_dependencies.set(model_deps)
        elif request.POST.get('app_action') == "Settings":
            
            
            print("UPDATING APP DEPLOYMENT")
            print(instance)
            instance.name = app_name
            instance.settings = str(request.POST.dict())
            instance.parameters=str(parameters_out)
            instance.action = "update"
            instance.save()
            instance.app_dependencies.set(app_deps)
            instance.vol_dependencies.set(vol_deps)
            instance.model_dependencies.set(model_deps)
        else:
            raise Exception("Incorrect action on app.")

        return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project.slug), 'category': instance.app.category.slug}))

    return render(request, template, locals())

def delete(request, user, project, ai_id):
    appinstance = AppInstance.objects.get(pk=ai_id)
    appinstance.helmchart.delete()
    return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': appinstance.app.category.slug}))