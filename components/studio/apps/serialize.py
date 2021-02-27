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

key_words = ['appobj', 'model', 'flavor', 'environment', 'volumes', 'apps', 'logs', 'permissions', 'keycloak-config', 'csrfmiddlewaretoken']

def serialize_model(form_selection):
    print("SERIALIZING MODEL")
    model_json = dict()
    obj = []
    if 'model' in form_selection:
        model_id = form_selection.get('model', None)
        obj = Model.objects.filter(pk=model_id)
        print("Fetching selected model:")

        
        # model_json['model'] = dict()
        keys = get_minio_keys(obj[0].project)
        model_json = {
            "model": {
                "name": obj[0].name,
                "version": obj[0].version,
                "release_type": obj[0].release_type,
                "description": obj[0].description,
                "url": "https://{}".format(obj[0].s3.host),
                "access_key": obj[0].s3.access_key,
                "secret_key": obj[0].s3.secret_key,
                "bucket": "models",
                "obj": obj[0].uid
            }
        }

    return model_json, obj

def serialize_flavor(form_selection):
    print("SERIALIZING FLAVOR")
    flavor_json = dict()
    if 'flavor' in form_selection:
        flavor_id = form_selection.get('flavor', None)
        flavor = Flavor.objects.get(pk=flavor_id)

        flavor_json['flavor'] = {
            "requests": {
                "cpu": flavor.cpu,
                "memory": flavor.mem
            },
            "limits": {
                "cpu": flavor.cpu,
                "memory": flavor.mem
            },
            "gpu": {
                "enabled": False
            }
        }
        if flavor.gpu and flavor.gpu > 0:
            flavor_json['flavor']['gpu']['enabled'] = True

    return flavor_json

def serialize_environment(form_selection):
    print("SERIALIZING ENVIRONMENT")
    environment_json = dict()
    if 'environment' in form_selection:
        environment_id = form_selection.get('environment', None)
        environment = Environment.objects.get(pk=environment_id)
        environment_json['environment'] = {
            "pk": environment.pk,
            "repository": environment.repository,
            "image": environment.image,
            "registry": False
        }
        if environment.registry:
            environment_json['environment']['registry'] = environment.registry.parameters
            environment_json['environment']['registry']['enabled'] = True
        else:
            environment_json['environment']['registry'] = {"enabled": False}
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
                parameters['apps'][app.slug][slugify(obj.name)] = obj.parameters

    return parameters, app_deps


def serialize_primitives(form_selection):
    print("SERIALIZING PRIMITIVES")
    parameters = dict()
    keys = form_selection.keys()
    for key in keys:
        if key not in key_words and 'app:' not in key:
            parameters[key] = form_selection[key].replace('\r\n', '\n')
            if parameters[key] == "False":
                parameters[key] = False
            elif parameters[key] == "True":
                parameters[key] = True
    print(parameters)
    return flatten_json.unflatten(parameters, '.')

def serialize_permissions(form_selection):
    print("SERIALIZING PERMISSIONS")
    parameters = dict()
    parameters['permissions'] = {
        "public": False,
        "project": False,
        "private": False
    }

    permission = form_selection.get('permission', None)
    parameters['permissions'][permission] = True
    print(parameters)
    return parameters

def serialize_appobjs(form_selection):
    print("SERIALIZING APPOBJS")
    parameters = dict()
    appobjs = []
    if 'appobj' in form_selection:
        appobjs = form_selection.getlist('appobj')
        parameters['appobj'] = dict()
        for obj in appobjs:
            app = Apps.objects.get(pk=obj)
            parameters['appobj'][app.slug] = True
    print(parameters)
    return parameters

def serialize_app(form_selection):
    print("SERIALIZING APP")
    parameters = dict()

    model_params, model_deps = serialize_model(form_selection)
    parameters.update(model_params)

    app_params, app_deps = serialize_apps(form_selection)
    parameters.update(app_params)

    prim_params = serialize_primitives(form_selection)
    parameters.update(prim_params)

    flavor_params = serialize_flavor(form_selection)
    parameters.update(flavor_params)

    environment_params = serialize_environment(form_selection)
    parameters.update(environment_params)

    permission_params = serialize_permissions(form_selection)
    parameters.update(permission_params)

    appobj_params = serialize_appobjs(form_selection)
    parameters.update(appobj_params)

    return parameters, app_deps, model_deps