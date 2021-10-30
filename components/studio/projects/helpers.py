from .exceptions import ProjectCreationException
from django.conf import settings

import base64
import requests as r
import yaml
import re
import time

#import modules.keycloak_lib as keylib
#from .tasks import create_keycloak_client_task

def urlify(s):

    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '-', s)

    return s

"""
def create_project_resources(project, username, repository=None):
    res1 = create_keycloak_client_task.delay(project.slug, username, [])
    # Wait for keycloak task to finish before returning (otherwise user wouldn't have
    # correct Keycloak roles)
    while not res1.ready():
        time.sleep(0.1)


def delete_project_resources(project):
    kc = keylib.keycloak_init()
    keylib.keycloak_delete_client(kc, project.slug)
    
    scope_id, res_json = keylib.keycloak_get_client_scope_id(kc, project.slug+'-scope')
    keylib.keycloak_delete_client_scope(kc, scope_id)
    return True
"""


def get_minio_keys(project):
    return {
        'project_key': decrypt_key(project.project_key),
        'project_secret': decrypt_key(project.project_secret)
    }


def decrypt_key(key):
    base64_bytes = key.encode('ascii')
    result = base64.b64decode(base64_bytes)
    return result.decode('ascii')
