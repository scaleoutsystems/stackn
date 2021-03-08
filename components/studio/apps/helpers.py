from django.shortcuts import render, HttpResponseRedirect, reverse
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q
from django.template import engines
from .models import Apps, AppInstance, AppCategories, AppPermission, AppStatus
from projects.models import Project, Flavor, Environment
from models.models import Model
from projects.helpers import get_minio_keys
import modules.keycloak_lib as keylib
from .serialize import serialize_app
from .tasks import deploy_resource, delete_resource
import requests
import flatten_json
import uuid
from datetime import datetime, timedelta
from .generate_form import generate_form

def create_instance_params(instance, action="create"):
    RELEASE_NAME = instance.app.slug.replace('_', '-')+'-'+instance.project.slug+'-'+uuid.uuid4().hex[0:4]
    print("RELEASE_NAME: "+RELEASE_NAME)

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
        # "project": {
        #     "name": instance.project.name,
        #     "slug": instance.project.slug
        # },
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
    if 'project' not in instance.parameters:
        instance.parameters['project'] = dict()
    instance.parameters['project'].update({'name': instance.project.name, 'slug': instance.project.slug})


    # Add field for table.    
    if instance.app.table_field and instance.app.table_field != "":
        django_engine = engines['django']
        info_field = django_engine.from_string(instance.app.table_field).render(parameters)
        instance.table_field = info_field
    else:
        instance.table_field = ""