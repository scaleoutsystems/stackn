import time
import uuid

from django.apps import apps
from django.conf import settings
from django.template import engines

from ..models import AppInstance, AppStatus  # type: ignore
from ..serialize import serialize_app  # type: ignore
from ..tasks import deploy_resource  # type: ignore

ReleaseName = apps.get_model(app_label=settings.RELEASENAME_MODEL)


def create_instance_params(instance, action="create"):
    print("HELPER - CREATING INSTANCE PARAMS")
    RELEASE_NAME = "r" + uuid.uuid4().hex[0:8]
    print("RELEASE_NAME: " + RELEASE_NAME)

    SERVICE_NAME = RELEASE_NAME + "-" + instance.app.slug
    # TODO: Fix for multicluster setup, look at e.g. labs
    HOST = settings.DOMAIN
    AUTH_HOST = settings.AUTH_DOMAIN
    AUTH_PROTOCOL = settings.AUTH_PROTOCOL
    NAMESPACE = settings.NAMESPACE

    # Add some generic parameters.
    parameters = {
        "release": RELEASE_NAME,
        "chart": str(instance.app.chart),
        "namespace": NAMESPACE,
        "app_slug": str(instance.app.slug),
        "app_revision": str(instance.app.revision),
        "appname": RELEASE_NAME,
        "global": {
            "domain": HOST,
            "auth_domain": AUTH_HOST,
            "protocol": AUTH_PROTOCOL,
        },
        "s3sync": {"image": "scaleoutsystems/s3-sync:latest"},
        "service": {
            "name": SERVICE_NAME,
            "port": instance.parameters["default_values"]["port"],
            "targetport": instance.parameters["default_values"]["targetport"],
        },
        "storageClass": settings.STORAGECLASS,
    }

    instance.parameters.update(parameters)

    if "project" not in instance.parameters:
        instance.parameters["project"] = dict()

    instance.parameters["project"].update({"name": instance.project.name, "slug": instance.project.slug})


def can_access_app_instance(app_instance, user, project):
    """Checks if a user has access to an app instance

    Args:
        app_instance (AppInstance): app instance object
        user (User): user object
        project (Project): project object

    Returns:
        Boolean: returns False if user lack permission to provided app instance
    """
    authorized = False

    if app_instance.access == "public":
        authorized = True
    elif app_instance.access == "project":
        if user.has_perm("can_view_project", project):
            authorized = True
    else:
        if user.has_perm("can_access_app", app_instance):
            authorized = True

    return authorized


def can_access_app_instances(app_instances, user, project):
    """Checks if user has access to all app instances provided

    Args:
        app_instances (Queryset<AppInstace>): list of app instances
        user (User): user object
        project (Project): project object

    Returns:
        Boolean: returns False if user lacks
        permission to any of the app instances provided
    """
    for app_instance in app_instances:
        authorized = can_access_app_instance(app_instance, user, project)

        if not authorized:
            return False

    return True


def handle_permissions(parameters, project):
    access = ""

    if parameters["permissions"]["public"]:
        access = "public"
    elif parameters["permissions"]["project"]:
        access = "project"

        if "project" not in parameters:
            parameters["project"] = dict()

        parameters["project"]["client_id"] = project.slug
        parameters["project"]["client_secret"] = project.slug
        parameters["project"]["slug"] = project.slug
        parameters["project"]["name"] = project.name

    elif parameters["permissions"]["private"]:
        access = "private"

    return access


def create_app_instance(user, project, app, app_settings, data=[], wait=False):
    app_name = data.get("app_name")

    parameters_out, app_deps, model_deps = serialize_app(data, project, app_settings, user.username)

    authorized = can_access_app_instances(app_deps, user, project)

    if not authorized:
        raise Exception("Not authorized to use specified app dependency")

    access = handle_permissions(parameters_out, project)

    app_instance = AppInstance(
        name=app_name,
        access=access,
        app=app,
        project=project,
        info={},
        parameters=parameters_out,
        owner=user,
    )

    create_instance_params(app_instance, "create")

    # Attempt to create a ReleaseName model object
    rel_name_obj = []
    if "app_release_name" in data and data.get("app_release_name") != "":
        submitted_rn = data.get("app_release_name")
        try:
            rel_name_obj = ReleaseName.objects.get(name=submitted_rn, project=project, status="active")
            rel_name_obj.status = "in-use"
            rel_name_obj.save()
            app_instance.parameters["release"] = submitted_rn
        except Exception as e:
            print("Error: Submitted release name not owned by project.")
            print(e)
            return [False, None, None]

    # Add fields for apps table:
    # to be displayed as app details in views
    if app_instance.app.table_field and app_instance.app.table_field != "":
        django_engine = engines["django"]
        info_field = django_engine.from_string(app_instance.app.table_field).render(app_instance.parameters)
        app_instance.table_field = eval(info_field)
    else:
        app_instance.table_field = {}

    # Setting status fields before saving app instance
    status = AppStatus(appinstance=app_instance)
    status.status_type = "Created"
    status.info = app_instance.parameters["release"]
    app_instance.save()
    # Saving ReleaseName, permissions, status and
    # setting up dependencies
    if rel_name_obj:
        rel_name_obj.app = app_instance
        rel_name_obj.save()
    status.save()
    app_instance.app_dependencies.set(app_deps)
    app_instance.model_dependencies.set(model_deps)

    # Finally, attempting to create apps resources
    res = deploy_resource.delay(app_instance.pk, "create")

    # wait is passed as a function parameter
    if wait:
        while not res.ready():
            time.sleep(0.1)

    return [True, project.slug, app_instance.app.category.slug]
