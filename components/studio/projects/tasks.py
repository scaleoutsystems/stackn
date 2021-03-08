from celery import shared_task
import requests as r
import yaml
import base64

import modules.keycloak_lib as keylib

from .exceptions import ProjectCreationException

from django.conf import settings

@shared_task
def create_keycloak_client_task(project_slug, username, repository):
    # Create Keycloak client for project with default project role.
    # The creator of the project assumes all roles by default.
    print('Creating Keycloak resources.')
    HOST = settings.DOMAIN
    RELEASE_NAME = str(project_slug)
    # This is just a dummy URL -- it doesn't go anywhere.
    URL = 'https://{}/{}/{}'.format(HOST, username, RELEASE_NAME)

    
    client_id, client_secret, res_json = keylib.keycloak_setup_base_client(URL, RELEASE_NAME, username, settings.PROJECT_ROLES, settings.PROJECT_ROLES)
    if not res_json['success']:
        print("ERROR: Failed to create keycloak client for project.")
    else:
        print('Done creating Keycloak client for project.')


def create_settings_file(project_slug):
    proj_settings = dict()
       
    proj_settings['active'] = 'stackn'
    proj_settings['client_id'] = 'studio-api'
    proj_settings['realm'] = settings.KC_REALM
    proj_settings['active_project'] = project_slug

    return yaml.dump(proj_settings)
