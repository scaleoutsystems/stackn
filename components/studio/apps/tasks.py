from celery import shared_task
from modules import keycloak_lib as keylib
from django.conf import settings
import chartcontroller.controller as controller
from .models import AppInstance


def add_valid_redirect_uri(project_slug, URI):
    print("Adding valid redirect.")

    

    kc = keylib.keycloak_init()
    print(project_slug)
    print(URI)
    res = keylib.keycloak_add_client_valid_redirect(kc, project_slug, URI)

@shared_task
def deploy_resource(instance_pk, action='create'):

    instance = AppInstance.objects.get(pk=instance_pk)
    username = str(instance.owner)
    # If app is new, we need to create a Keycloak client.
    if action == "create":

        
        parameters = instance.parameters

        # Add redirect URI to project client
        if settings.OIDC_VERIFY_SSL:
            URI =  'https://'+parameters['release']+'.'+parameters['global']['domain']
        else:
            URI =  'http://'+parameters['release']+'.'+parameters['global']['domain']

        add_valid_redirect_uri(parameters['project']['slug'], URI.strip('/')+'/*')

        # KC_URL = URI.strip('/')+'/*'
        print("Creating Keycloak client")
        # print(KC_URL)
        print(parameters)
        print(username)
        client_id, client_secret = keylib.keycloak_setup_base_client(URI, parameters['release'], username, ['owner'], ['owner'])
        print(client_id)
        print(client_secret)
        gatekeeper = {
            "gatekeeper": {
                "realm": settings.KC_REALM,
                "client_secret": client_secret,
                "client_id": client_id,
                "auth_endpoint": settings.OIDC_OP_REALM_AUTH,
            }
        }
        parameters.update(gatekeeper)
        
        instance.parameters = parameters
        instance.save()
        print(":::::::::::::::::::::::::::;")

    # Deploy resource.
    controller.deploy(instance.parameters)

@shared_task
def delete_resource(parameters):
    print("Uninstalling resource.")
    controller.delete(parameters)