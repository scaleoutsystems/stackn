import flatten_json
from django.db.models import Q

from models.models import Model
from projects.models import S3, Environment, Flavor, ReleaseName

from .models import AppInstance, Apps

key_words = [
    "appobj",
    "model",
    "flavor",
    "environment",
    "volumes",
    "apps",
    "logs",
    "permissions",
    "default_values",
    "export-cli",
    "csrfmiddlewaretoken",
    "S3",
    "env_variables",
    "publishable",
]


def get_form_models(aset, project, appinstance=[]):
    dep_model = False
    models = []
    if "model" in aset:
        print("app requires a model")
        dep_model = True
        if "object_type" in aset["model"]:
            object_type = aset["model"]["object_type"]
        else:
            object_type = "default"
        models = Model.objects.filter(project=project, object_type__slug=object_type)

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
    if "apps" in aset:
        dep_apps = True
        app_deps = dict()
        apps = aset["apps"]
        for app_name, option_type in apps.items():
            print(">>>>>")
            print(app_name)
            # .order_by('-revision').first()
            app_obj = Apps.objects.filter(name=app_name)
            print(app_obj)
            print(">>>>>")
            # TODO: Only get app instances that we have permission to list.

            app_instances = AppInstance.objects.filter(
                ~Q(state="Deleted"),
                Q(owner=user) | Q(access__in=["project", "public"]),
                project=project,
                app__name=app_name,
            )
            # TODO: Special case here for "environment" app.
            # Could be solved by supporting "condition":
            # '"appobj.app_slug":"true"'
            if app_name == "Environment":
                app_instances = AppInstance.objects.filter(
                    ~Q(state="Deleted"),
                    Q(owner=user) | Q(access__in=["project", "public"]),
                    project=project,
                    app__name=app_name,
                    parameters__contains={"appobj": {myapp.slug: True}},
                )

            for ain in app_instances:
                if appinstance and ain.appinstance_set.filter(pk=appinstance.pk).exists():
                    ain.selected = "selected"
                else:
                    ain.selected = ""

            if option_type == "one":
                app_deps[app_name] = {
                    "instances": app_instances,
                    "option_type": "",
                }
            else:
                app_deps[app_name] = {
                    "instances": app_instances,
                    "option_type": "multiple",
                }
    return dep_apps, app_deps


def get_form_primitives(aset, project, appinstance=[]):
    all_keys = aset.keys()
    print("PRIMITIVES")
    primitives = dict()
    if appinstance:
        ai_vals = flatten_json.flatten(appinstance.parameters, ".")
    for key in all_keys:
        if key not in key_words:
            primitives[key] = aset[key]
            if "meta" in primitives[key]:
                primitives[key]["meta_title"] = primitives[key]["meta"]["title"]
            else:
                primitives[key]["meta_title"] = key
            if appinstance:
                for subkey, subval in aset[key].items():
                    print(subkey)
                    try:
                        if subkey != "meta" and subkey != "meta_title":
                            primitives[key][subkey]["default"] = ai_vals[key + "." + subkey]
                    except Exception as err:
                        print(err)
    print(primitives)
    return primitives


def get_form_permission(aset, project, appinstance=[]):
    form_permissions = {
        "public": {"value": "false", "option": "false"},
        "project": {"value": "false", "option": "false"},
        "private": {"value": "true", "option": "true"},
    }
    dep_permissions = True
    if "permissions" in aset:
        form_permissions = aset["permissions"]
        # if not form_permissions:
        #     dep_permissions = False

        if appinstance:
            try:
                ai_vals = appinstance.parameters
                print(ai_vals["permissions"])
                form_permissions["public"]["value"] = ai_vals["permissions"]["public"]
                form_permissions["project"]["value"] = ai_vals["permissions"]["project"]
                form_permissions["private"]["value"] = ai_vals["permissions"]["private"]
                print(form_permissions)
            except Exception as err:
                print(err)
                print("Permissions not set for app instance, using default.")
    return dep_permissions, form_permissions


def get_form_appobj(aset, project, appinstance=[]):
    print("CHECKING APP OBJ")
    dep_appobj = False
    appobjs = dict()
    if "appobj" in aset:
        print("NEEDS APP OBJ")
        dep_appobj = True
        appobjs["objs"] = Apps.objects.all()
        appobjs["title"] = aset["appobj"]["title"]
        appobjs["type"] = aset["appobj"]["type"]

    print(appobjs)
    return dep_appobj, appobjs


def get_form_environments(aset, project, app, appinstance=[]):
    print("CHECKING ENVIRONMENT")
    dep_environment = False
    environments = dict()
    if "environment" in aset:
        dep_environment = True
        if aset["environment"]["type"] == "match":
            environments["objs"] = Environment.objects.filter(project=project, app__slug=app.slug)
        elif aset["environment"]["type"] == "any":
            environments["objs"] = Environment.objects.filter(project=project)
        elif "apps" in aset["environment"]:
            environments["objs"] = Environment.objects.filter(
                project=project, app__slug__in=aset["environment"]["apps"]
            )

        environments["title"] = aset["environment"]["title"]
        if appinstance:
            ai_vals = appinstance.parameters
            environments["selected"] = ai_vals["environment"]["pk"]

    return dep_environment, environments


def get_form_S3(aset, project, app, appinstance=[]):
    print("CHECKING S3")
    dep_S3 = False
    s3stores = []
    if "S3" in aset:
        dep_S3 = True
        s3stores = S3.objects.filter(project=project)
    return dep_S3, s3stores


def generate_form(aset, project, app, user, appinstance=[]):
    form = dict()
    form["dep_model"], form["models"] = get_form_models(aset, project, appinstance)
    form["dep_apps"], form["app_deps"] = get_form_apps(aset, project, app, user, appinstance)
    form["dep_appobj"], form["appobjs"] = get_form_appobj(aset, project, appinstance)
    form["dep_environment"], form["environments"] = get_form_environments(aset, project, app, appinstance)
    form["dep_S3"], form["s3stores"] = get_form_S3(aset, project, app, appinstance)

    form["dep_vols"] = False
    form["dep_flavor"] = False
    if "flavor" in aset:
        form["dep_flavor"] = True
        form["flavors"] = Flavor.objects.filter(project=project)

    form["primitives"] = get_form_primitives(aset, project, appinstance)
    form["dep_permissions"], form["form_permissions"] = get_form_permission(aset, project, appinstance)
    release_names = ReleaseName.objects.filter(project=project, status="active")
    form["release_names"] = release_names
    return form
