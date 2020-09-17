from celery import shared_task
import requests as r
import yaml
import base64

import modules.keycloak_lib as keylib
# from .helpers import decrypt_key
from .exceptions import ProjectCreationException

from django.conf import settings

@shared_task
def create_keycloak_client_task(project_slug, username, repository):
    # Create Keycloak client for project with default project role.
    # The creator of the project assumes all roles by default.
    print('Creating Keycloak resources.')
    HOST = settings.DOMAIN
    print('host: '+HOST)
    RELEASE_NAME = str(project_slug)
    print('release: '+RELEASE_NAME)
    URL = 'https://{}/{}/{}'.format(HOST, username, RELEASE_NAME)
    print(URL)
    
    keylib.keycloak_setup_base_client(URL, RELEASE_NAME, username, settings.PROJECT_ROLES, settings.PROJECT_ROLES)

    print('Done Keycloak.')


def create_settings_file(project_slug):
    proj_settings = dict()
       
    proj_settings['active'] = 'stackn'
    proj_settings['client_id'] = 'studio-api'
    proj_settings['realm'] = settings.KC_REALM
    proj_settings['active_project'] = project_slug

    return yaml.dump(proj_settings)

def decrypt_key(key):
    base64_bytes = key.encode('ascii')
    result = base64.b64decode(base64_bytes)
    return result.decode('ascii')

@shared_task
def create_helm_resources_task(project_slug, project_key, project_secret, repository=None):

    proj_settings = create_settings_file(project_slug)
    parameters = {'release': str(project_slug),
                  'chart': 'project',
                  'minio.access_key': decrypt_key(project_key),
                  'minio.secret_key': decrypt_key(project_secret),
                  'global.domain': settings.DOMAIN,
                  'storageClassName': settings.STORAGECLASS,
                  'settings_file': proj_settings}
    if repository:
        parameters.update({'labs.repository': repository})

    url = settings.CHART_CONTROLLER_URL + '/deploy'

    retval = r.get(url, parameters)
    print("CREATE_PROJECT:helm chart creator returned {}".format(retval))

    if retval.status_code >= 200 or retval.status_code < 205:
        # return True
        print('DONE CREATING PROJECT HELM DEPLOYMENT')
    else:
        print('FAILED TO CREATE PROJECT HELM DEPLOYMENT')
        raise ProjectCreationException(__name__)