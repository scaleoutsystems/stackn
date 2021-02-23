import os
import subprocess
import json
import time
from celery import shared_task
# from celery.decorators import periodic_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from datetime import datetime
import time
from modules import keycloak_lib as keylib
import chartcontroller.controller as controller
from .models import AppInstance, ResourceData, AppStatus
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
    stderr = results.stderr.decode('utf-8')
    # stdout = stdout.split('\n')
    # res_json = dict()
    # print("PROCESSING STDOUT")
    # for line in stdout:
    #     if line != '':
    #         print(line)
    #         tmp = line.split(':')
    #         if len(tmp) == 2:
    #             res_json[tmp[0]] = tmp[1]
    return stdout, stderr

@shared_task
@transaction.atomic
def deploy_resource(instance_pk, action='create'):

    instance = AppInstance.objects.select_for_update().get(pk=instance_pk)
    username = str(instance.owner)
    # If app is new, we need to create a Keycloak client.
    keycloak_success = True
    if action == "create":

        parameters = instance.parameters
        
        status = AppStatus(appinstance=instance)
        status.status_type = 'Failed'
        status.info = parameters['release']

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
            status.status_type = "Failed"
        # else:
        #     instance.state = "Installing"

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
        stdout, stderr = process_helm_result(results)
        if results.returncode == 0:
            print("Helm install succeeded")
            status.status_type = "Installed"
            helm_info = {
                "success": True,
                "info": {
                    "stdout": stdout,
                    "stderr": stderr
                }
            }
        else:
            print("Helm install failed")
            status.status_type = "Failed"
            helm_info = {
                "success": False,
                "info": {
                    "stdout": stdout,
                    "stderr": stderr
                }
            }

        instance.info["helm"] = helm_info
        instance.save()
        status.save()


@shared_task
@transaction.atomic
def delete_resource(pk):
    appinstance = AppInstance.objects.select_for_update().get(pk=pk)
    

    if appinstance and appinstance.state != "Deleted":
        # The instance does exist.
        parameters = appinstance.parameters
        # TODO: Check that the user has the permission required to delete it.

        # Clean up in Keycloak.
        kc = keylib.keycloak_init()
        # TODO: Fix for multicluster setup
        # TODO: We are assuming this URI here, but we should allow for other forms.
        # The instance should store information about this.
        URI =  'https://'+appinstance.parameters['release']+'.'+settings.DOMAIN
        
        try:
            keylib.keycloak_remove_client_valid_redirect(kc, appinstance.project.slug, URI.strip('/')+'/*')
            keylib.keycloak_delete_client(kc, appinstance.parameters['gatekeeper']['client_id'])
            scope_id, res_json = keylib.keycloak_get_client_scope_id(kc, appinstance.parameters['gatekeeper']['client_id']+'-scope')
            if not res_json['success']:
                print("Failed to get client scope.")
            else:
                keylib.keycloak_delete_client_scope(kc, scope_id)
        except:
            print("Failed to clean up in Keycloak.")
        
        
        
        # Delete installed resources on the cluster.
        release = appinstance.parameters['release']
        namespace = appinstance.parameters['namespace']



    results = controller.delete(parameters)
    if results.returncode == 0 or 'release: not found' in results.stderr.decode('utf-8'):
        status = AppStatus(appinstance=appinstance)
        status.status_type = "Terminated"
        status.save()
    else:
        status = AppStatus(appinstance=appinstance)
        status.status_type = "FailedToDelete"
        status.save()
        # appinstance.state = "FailedToDelete"

    # print("NEW STATE:")
    # print(appinstance.state)
    # appinstance.save()
    # for i in range(0,15):
    #     appinstance =  AppInstance.objects.get(pk=pk)
    #     print("FETCHED STATE:")
    #     print(appinstance.state)
    #     appinstance.save()
    # return results.returncode, results.stdout.decode('utf-8')

@app.task
def check_status():
    volume_root = "/"
    if "TELEPRESENCE_ROOT" in os.environ:
        volume_root = os.environ["TELEPRESENCE_ROOT"]
    kubeconfig = os.path.join(volume_root, 'app/chartcontroller/config/config')

    # TODO: Fix for multicluster setup.
    args = ['kubectl', '--kubeconfig', kubeconfig, '-n', settings.NAMESPACE, 'get', 'po', '-l', 'type=app', '-o', 'json']
    # print(args)
    results = subprocess.run(args, capture_output=True)
    # print(results)
    res_json = json.loads(results.stdout.decode('utf-8'))
    app_statuses = dict()
    # print(res_json)
    for item in res_json['items']:
        release = item['metadata']['labels']['release']
        phase = item['status']['phase']
        
        deletion_timestamp = []
        if 'deletionTimestamp' in item['metadata']:
            deletion_timestamp = item['metadata']['deletionTimestamp']
        num_containers = len(item['status']['containerStatuses'])
        num_cont_ready = 0
        if 'containerStatuses' in item['status']:
            for container in item['status']['containerStatuses']:
                if container['ready']:
                    num_cont_ready += 1
        app_statuses[release] = {
            "phase": phase,
            "num_cont": num_containers,
            "num_cont_ready": num_cont_ready,
            "deletion_status": deletion_timestamp
        }


    instances = AppInstance.objects.filter(~Q(state="Deleted"))
    for instance in instances:
        release = instance.parameters['release']
        if release in app_statuses:
            current_status = app_statuses[release]['phase']
            try:
                latest_status = AppStatus.objects.filter(appinstance=instance).latest('time').status_type
            except:
                latest_status = "Unknown"
            if current_status != latest_status:
                print("New status for release {}".format(release))
                print("Current status: {}".format(current_status))
                print("Previous status: {}".format(latest_status))
                status = AppStatus(appinstance=instance)
                if app_statuses[release]['deletion_status']:
                    status.status_type = "Terminated"
                else:
                    status.status_type = app_statuses[release]['phase']
                # status.info = app_statuses[release]
                status.save()
            # else:
            #     print("No update for release: {}".format(release))
        else:
            delete_exists = AppStatus.objects.filter(appinstance=instance, status_type="Terminated").exists()
            if delete_exists:
                status = AppStatus(appinstance=instance)
                status.status_type = "Deleted"
                status.save()                
                instance.state = "Deleted"
                instance.deleted_on = datetime.now()
                instance.save()
        # if instance.state != "Deleted":
        #     try:
        #         release = instance.parameters['release']
        #         instance.state = app_statuses[release]['phase']
        #         instance.save()
        #     except:
        #         if instance.app.slug != 'volume':
        #             instance.state = "Deleted"
        #             instance.save()
            # print("Release {} not in namespace.".format(release))
    # instances.save()
    # print(app_statuses)

@app.task
def get_resource_usage():

    volume_root = "/"
    if "TELEPRESENCE_ROOT" in os.environ:
        volume_root = os.environ["TELEPRESENCE_ROOT"]
    kubeconfig = os.path.join(volume_root, 'app/chartcontroller/config/config')

    timestamp = time.time()

    args = ['kubectl', '--kubeconfig', kubeconfig, 'get', '--raw', '/apis/metrics.k8s.io/v1beta1/pods']
    results = subprocess.run(args, capture_output=True)
    res_json = json.loads(results.stdout.decode('utf-8'))
    pods = res_json['items']

    resources = dict()

    args_pod = ['kubectl', '--kubeconfig', kubeconfig, 'get', 'po', '-o', 'json']
    results_pod = subprocess.run(args_pod, capture_output=True)
    results_pod_json = json.loads(results_pod.stdout.decode('utf-8'))
    for pod in results_pod_json['items']:
        if 'release' in pod['metadata']['labels'] and 'project' in pod['metadata']['labels']:
    #         pod_release = pod['metadata']['labels']['release']
    #         for label in pod['metadata']['labels']:
    #             resources[label] = pod['metadata']['labels'][label]
            pod_name = pod['metadata']['name']
            resources[pod_name] = dict()
            resources[pod_name]['labels'] = pod['metadata']['labels']
            resources[pod_name]['cpu'] = 0.0
            resources[pod_name]['memory'] = 0.0
            resources[pod_name]['gpu'] = 0

    for pod in pods:
        
        podname = pod['metadata']['name']
        if podname in resources:
            containers = pod['containers']
            cpu = 0
            mem = 0
            for container in containers:
                cpun = container['usage']['cpu']
                memki = container['usage']['memory']
                try:
                    cpu += int(cpun.replace('n', ''))/1e6
                except:
                    print("Failed to parse CPU usage:")
                    print(cpun)
                if 'Ki' in memki:
                    mem += int(memki.replace('Ki', ''))/1000
                elif 'Mi' in memki:
                    mem += int(memki.replace('Mi', ''))
                elif 'Gi' in memki:
                    mem += int(memki.replace('Mi', ''))*1000

            resources[podname]['cpu'] = cpu
            resources[podname]['memory'] = mem
            
    # print(json.dumps(resources, indent=2))

    for key in resources.keys():
        entry = resources[key]
        # print(entry['labels']['release'])
        appinstance = AppInstance.objects.get(parameters__contains={"release": entry['labels']['release']})
        # print(timestamp)
        # print(appinstance)
        # print(entry)
        datapoint = ResourceData(appinstance=appinstance, cpu=entry['cpu'], mem=entry['memory'], gpu=entry['gpu'], time=timestamp)
        datapoint.save()

    # print(timestamp)
    # print(json.dumps(resources, indent=2))  

