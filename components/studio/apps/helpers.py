from django.conf import settings
import uuid

def create_instance_params(instance, action="create"):
    print("HELPER - CREATING INSTANCE PARAMS")
    RELEASE_NAME = 'r'+uuid.uuid4().hex[0:8] #instance.app.slug.replace('_', '-')+'-'+instance.project.slug+'-'+uuid.uuid4().hex[0:4]
    print("RELEASE_NAME: "+RELEASE_NAME)

    SERVICE_NAME = RELEASE_NAME + '-' + instance.app.slug
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
        "s3sync": {
            "image": "scaleoutsystems/s3-sync:latest"
        },
        "service": {
            "name": SERVICE_NAME,
            "port": instance.parameters["default_values"]["port"],
            "targetport": instance.parameters["default_values"]["targetport"]
        },
        "storageClass": settings.STORAGECLASS
    }

    instance.parameters.update(parameters)
    
    if 'project' not in instance.parameters:
        instance.parameters['project'] = dict()
        
    instance.parameters['project'].update({'name': instance.project.name, 'slug': instance.project.slug})
