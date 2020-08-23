from celery import shared_task
# from .helpers import create_environment_image, create_helm_resources
import modules.keycloak_lib as keylib
from django.conf import settings

@shared_task
def create_keycloak_client_task(project_slug, username, repository):
    # create_environment_image(project, repository)
    # create_helm_resources(project, username, repository)
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