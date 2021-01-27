from .exceptions import ProjectCreationException
from django.conf import settings

import base64
import requests as r
import yaml
import re
import time

import modules.keycloak_lib as keylib
from .tasks import create_keycloak_client_task, create_helm_resources_task

def urlify(s):

    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '-', s)

    return s

    
def create_project_resources(project, username, cluster, repository=None):
    res1 = create_keycloak_client_task.delay(project.slug, username, [])
    res2 = create_helm_resources_task(project.slug, project.project_key, project.project_secret, cluster, username, repository)
    # Wait for keycloak task to finish before returning (otherwise user wouldn't have
    # correct Keycloak roles)
    while not res1.ready():
        time.sleep(0.1)


def delete_project_resources(project):
    # retval = r.get(settings.CHART_CONTROLLER_URL + '/delete?release={}'.format(str(project.slug)))

    # if retval:
    #     # Delete Keycloak project client
    #     kc = keylib.keycloak_init()
    #     keylib.keycloak_delete_client(kc, project.slug)
        
    #     scope_id = keylib.keycloak_get_client_scope_id(kc, project.slug+'-scope')
    #     keylib.keycloak_delete_client_scope(kc, scope_id)
    #     return True

    # return False
    try:
        from deployments.models import HelmResource
        helmresource = HelmResource.objects.get(name=str(project.slug))
        helmresource.delete()
    except Exception as e:
        print("Failed to delete project helm resource object.")
        print(e)

    # if retval:
        # Delete Keycloak project client
    kc = keylib.keycloak_init()
    keylib.keycloak_delete_client(kc, project.slug)
    
    scope_id = keylib.keycloak_get_client_scope_id(kc, project.slug+'-scope')
    keylib.keycloak_delete_client_scope(kc, scope_id)

    from models.models import Model
    models = Model.objects.filter(project=project)
    for model in models:
        model.status = 'AR'
        model.save()
    # project.delete()

    return True


def get_minio_keys(project):
    return {
        'project_key': decrypt_key(project.project_key),
        'project_secret': decrypt_key(project.project_secret)
    }


def decrypt_key(key):
    base64_bytes = key.encode('ascii')
    result = base64.b64decode(base64_bytes)
    return result.decode('ascii')
