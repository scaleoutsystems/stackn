from django.shortcuts import render, HttpResponseRedirect, reverse
from django.conf import settings
from django.utils.text import slugify
from .models import Apps, AppInstance, AppCategories
from projects.models import Project, Volume
from models.models import Model
from projects.helpers import get_minio_keys
import flatten_json


key_words = ['model', 'volumes', 'apps', 'csrfmiddlewaretoken']

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

def filtered(request, user, project, category):
    template = 'index_apps.html'
    cat_obj = AppCategories.objects.get(slug=category)
    apps = Apps.objects.filter(category=cat_obj)
    project = Project.objects.get(slug=project)

    appinstances = AppInstance.objects.filter(owner=request.user, app__category=cat_obj)
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
    return parameters, app_deps, vol_deps, model_deps


def create(request, user, project, app_slug):
    template = 'create.html'
    project = Project.objects.get(slug=project)
    app = Apps.objects.get(slug=app_slug)

    aset = eval(app.settings)

    # Set up form

    

    dep_model = False
    if 'model' in aset:
        print('app requires a model')
        dep_model = True
        models = Model.objects.filter(project=project)
        print(models)
    

    dep_apps = False
    if 'apps' in aset:
        dep_apps = True
        app_deps = dict()
        apps = aset['apps']
        for app_name, option_type in apps.items():
            print(app_name)
            app_obj = Apps.objects.get(name=app_name)
            app_instances = AppInstance.objects.filter(project=project, app=app_obj)
            if option_type == "one":
                app_deps[app_name] = {"instances": app_instances, "option_type": ""}
            else:
                app_deps[app_name] = {"instances": app_instances, "option_type": "multiple"}
            # for app_instance in app_instances:
                # app_deps[app_name].append(app_instance.app.name+'-'+str(app_instance.pk))
    
    dep_vols = False
    if 'volumes' in aset:
        dep_vols = True
        volumes = Volume.objects.filter(project_slug=project.slug)
        volume_type = ""
        if aset['volumes'] == "many":
            volume_type = "multiple"
            
        print(volumes)
        print(volume_type)

    all_keys = aset.keys()
    print("PRIMITIVES")
    primitives = dict()
    for key in all_keys:
        if key not in key_words:
            primitives[key] = aset[key]




    print("::::::::::::")


    dep_volumes = False
    if 'volumes' in aset:
        dep_volumes = True
        volumes = Volume.objects.filter(project_slug=project.slug)



    if request.method == "POST":
        print(request.POST)
        app_name = request.POST.get('app_name')
        parameters_out, app_deps, vol_deps, model_deps = serialize_app(request.POST)
        print("PARAMETERS OUT")
        print(parameters_out)
        print(".............")
        instance = AppInstance(name=app_name,
                               app=app,
                               project=project,
                               settings=str(request.POST),
                               parameters=str(parameters_out),
                               owner=request.user)
        
        instance.save()
        instance.app_dependencies.set(app_deps)
        instance.vol_dependencies.set(vol_deps)
        instance.model_dependencies.set(model_deps)

        return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project.slug), 'category': instance.app.category.slug}))
    # try:
    #     projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user)).distinct('pk')
    # except TypeError as err:
    #     projects = []
    #     print(err)
    
    # request.session['next'] = '/projects/'
    return render(request, template, locals())

def delete(request, user, project, ai_id):
    # print(appinstance)
    appinstance = AppInstance.objects.get(pk=ai_id)
    appinstance.helmchart.delete()
    return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': appinstance.app.category.slug}))