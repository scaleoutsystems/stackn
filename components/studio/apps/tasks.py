import os
import subprocess
import json
from celery import shared_task
# from celery.decorators import periodic_task
from django.conf import settings
import time
from modules import keycloak_lib as keylib
import chartcontroller.controller as controller
from .models import AppInstance
from studio.celery import app

def get_URI(parameters):
    if settings.OIDC_VERIFY_SSL:
        URI =  'https://'+parameters['release']+'.'+parameters['global']['domain']
    else:
        URI =  'http://'+parameters['release']+'.'+parameters['global']['domain']

    URI = URI.strip('/')
    return URI

def add_valid_redirect_uri(instance):
    print("Adding valid redirect.")
    URI = get_URI(instance.parameters)
    parameters = instance.parameters

    
    project_slug = parameters['project']['slug']


    kc = keylib.keycloak_init()
    res = keylib.keycloak_add_client_valid_redirect(kc, project_slug, URI+'/*')

    instance.info.update({
        "keycloak": {
            "add_valid_redirect": res
        }
    })
    instance.save()

    return res['success']

def process_helm_result(results):
    stdout = results.stdout.decode('utf-8')
    stdout = stdout.split('\n')
    res_json = dict()
    print("PROCESSING STDOUT")
    for line in stdout:
        if line != '':
            print(line)
            tmp = line.split(':')
            if len(tmp) == 2:
                res_json[tmp[0]] = tmp[1]
    return res_json

@shared_task
def deploy_resource(instance_pk, action='create'):

    instance = AppInstance.objects.get(pk=instance_pk)
    username = str(instance.owner)
    # If app is new, we need to create a Keycloak client.
    keycloak_success = True
    if action == "create":

        parameters = instance.parameters
        URI = get_URI(parameters)
        # Set up Keycloak:
        # Add valid redirect URI to project client (for permission: project to work)
        # Create client for new resource
        
 
        if not add_valid_redirect_uri(instance):
            keycloak_success = False

        print(parameters)
        print("IN DEPLOY_RESOURCE: RELEASE:")
        print(parameters['release'])
        client_id, client_secret, res_json = keylib.keycloak_setup_base_client(URI, parameters['release'], username, ['owner'], ['owner'])
        if not res_json['success']:
            keycloak_success = False
        instance.info['keycloak'].update({"keycloak_setup_base_client": res_json})
        instance.save()

        if not keycloak_success:
            print("Failed to setup Keycloak client for resource.")
            print(instance.info['keycloak'])
            instance.state = "Failed"
        else:
            instance.state = "Installing"

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
        # Keycloak DONE.

    # Deploy resource.
    if keycloak_success:
        instance.info['keycloak'].update({"success": True})
        print("Deploying resource")
        results = controller.deploy(instance.parameters)
        res_json = process_helm_result(results)
        if results.returncode == 0:
            print("Helm install succeeded")
            instance.state = "Installed"
            helm_info = {
                "success": True,
                "info": {
                    "stdout": res_json
                }
            }
        else:
            print("Helm install failed")
            instance.state = "Failed"
            helm_info = {
                "success": False,
                "info": {
                    "stdout": res_json
                }
            }

        instance.info["helm"] = helm_info
        instance.save()


@shared_task
def delete_resource(parameters):
    print("Uninstalling resource.")
    results = controller.delete(parameters)
    return results.returncode, results.stdout.decode('utf-8')

@app.task
def test(arg):
    print(arg, flush=True)

@app.task
def check_status():
    volume_root = "/"
    if "TELEPRESENCE_ROOT" in os.environ:
        volume_root = os.environ["TELEPRESENCE_ROOT"]
    kubeconfig = os.path.join(volume_root, 'app/chartcontroller/config/config')

    # TODO: Fix for multicluster setup.
    args = ['kubectl', '--kubeconfig', kubeconfig, '-n', settings.NAMESPACE, 'get', 'po', '-l', 'type=app', '-o', 'json']
    print(args)
    results = subprocess.run(args, capture_output=True)
    # print(results)
    res_json = json.loads(results.stdout.decode('utf-8'))
    app_statuses = dict()
    # print(res_json)
    for item in res_json['items']:
        release = item['metadata']['labels']['release']
        phase = item['status']['phase']
        num_containers = len(item['status']['containerStatuses'])
        num_cont_ready = 0
        for container in item['status']['containerStatuses']:
            if container['ready']:
                num_cont_ready += 1
        app_statuses[release] = {
            "phase": phase,
            "num_cont": num_containers,
            "num_cont_ready": num_cont_ready
        }
    instances = AppInstance.objects.all()
    for instance in instances:
        try:
            release = instance.parameters['release']
            instance.state = app_statuses[release]['phase']
            instance.save()
        except:
            instance.state = "UnknownError"
            print("Release {} not in namespace.".format(release))
    # instances.save()
    print(app_statuses)

