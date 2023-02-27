import uuid

from django.conf import settings


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

    instance.parameters["project"].update(
        {"name": instance.project.name, "slug": instance.project.slug}
    )


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
