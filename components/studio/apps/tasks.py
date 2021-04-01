import os
import subprocess
import json
import time
import requests
from celery import shared_task
# from celery.decorators import periodic_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from datetime import datetime
import time
from modules import keycloak_lib as keylib
import chartcontroller.controller as controller
from .models import AppInstance, ResourceData, AppStatus, Apps
from models.models import Model, ObjectType
from projects.models import S3, Environment, MLFlow, BasicAuth
from studio.celery import app

def get_URI(parameters):
    URI =  'https://'+parameters['release']+'.'+parameters['global']['domain']

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

def post_create_hooks(instance):
    # hard coded hooks for now, we can make this dynamic and loaded from the app specs
    if instance.app.slug == 'minio':
        # Create a user role mapper for SSO (mapping readwrite role to 'minio_policy' claim.):
        kc = keylib.keycloak_init()
        client_id = instance.parameters['release']
        scope_id, res_json = keylib.keycloak_get_client_scope_id(kc, client_id+'-scope')
        res_json = keylib.keycloak_create_scope_mapper_roles(kc, scope_id, client_id, client_id+'-role-mapper', 'minio-policy')
        
        if not res_json['success']:
            print("Failed to create user role mapper for Minio instance: {}".format(instance.parameters['release']))
            # TODO: Update instance to reflect failure (User can still log in with root credentials)

        # Allow implicit flow for client:
        res_json = keylib.keycloak_client_allow_implicit_flow(kc, client_id)
        if not res_json['success']:
            print("Failed to allow implicit flow for Minio instance client: {}".format(instance.parameters['release']))
            # TODO: Update instance to reflect failure (User can still log in with root credentials)

        # Create project S3 object
        # TODO: If the instance is being updated, update the existing S3 object.
        access_key = instance.parameters['credentials']['access_key']
        secret_key = instance.parameters['credentials']['secret_key']
        host = '{}.{}'.format(instance.parameters['release'], instance.parameters['global']['domain'])
        try:
            s3obj = instance.s3obj
            s3obj.access_key = access_key
            s3obj.secret_key = secret_key
            s3obj.host = host
        except:
            s3obj = S3(name=instance.name,
                        project=instance.project,
                        host=host,
                        access_key=access_key,
                        secret_key=secret_key,
                        app=instance,
                        owner=instance.owner)
        s3obj.save()

    if instance.app.slug == 'environment':
        params = instance.parameters
        image = params['container']['name']
        # We can assume one registry here
        for reg_key in params['apps']['docker_registry'].keys():
            reg_release = params['apps']['docker_registry'][reg_key]['release']
            reg_domain = params['apps']['docker_registry'][reg_key]['global']['domain']
        repository = reg_release+'.'+reg_domain
        registry = AppInstance.objects.get(parameters__contains={
                                                        'release':reg_release
                                                    })

        target_environment = Environment.objects.get(pk=params['environment']['pk'])
        target_app = target_environment.app

        env_obj = Environment(name=instance.name,
                              project=instance.project,
                              repository=repository,
                              image=image,
                              registry=registry,
                              app=target_app,
                              appenv=instance)
        env_obj.save()

    if instance.app.slug == 'mlflow':
        params = instance.parameters
        s3 = S3.objects.get(pk=instance.parameters['s3']['pk'])
        basic_auth = BasicAuth(owner=instance.owner,
                               name=instance.name,
                               project=instance.project,
                               username=instance.parameters['credentials']['username'],
                               password=instance.parameters['credentials']['password'])
        basic_auth.save()
        obj = MLFlow(name=instance.name,
                     project=instance.project,
                     mlflow_url='https://{}.{}'.format(instance.parameters['release'], instance.parameters['global']['domain']),
                     s3=s3,
                     basic_auth=basic_auth,
                     app=instance,
                     owner=instance.owner)
        obj.save()


def post_delete_hooks(instance):
    if instance.app.slug == 'minio':
        try:
            s3obj = instance.s3obj
            s3obj.delete()
        except:
            print("S3 object not connected to a Minio App")
    
    if instance.app.slug == 'environment':
        print("POST DELETE ENVIRONMENT APP")
        try:
            env_obj = instance.envobj.all().delete()
        except:
            print("Didn't find any associated environment to delete.")
    
    if instance.app.slug == 'mlflow':
        try:
            mlflow_obj = instance.mlflowobj
            mlflow_obj.delete()
        except:
            print("MLFlow instance has no project MLFlow meta object.")

@shared_task
@transaction.atomic
def deploy_resource(instance_pk, action='create'):

    instance = AppInstance.objects.select_for_update().get(pk=instance_pk)
    username = str(instance.owner)
    status = AppStatus(appinstance=instance)
    # If app is new, we need to create a Keycloak client.
    keycloak_success = True
    if action == "create":

        parameters = instance.parameters
        
        
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

        # Default keycloak roles if none specified in config:
        keycloak_roles = ['owner']
        keycloak_default_roles = ['owner']
        # Check if app defines custom Keycloak roles and default roles:
        if 'keycloak-config' in instance.app.settings:
            keycloak_roles = instance.app.settings['keycloak-config']['roles']
            keycloak_default_roles = instance.app.settings['keycloak-config']['default-roles']


        client_id, client_secret, res_json = keylib.keycloak_setup_base_client(URI,
                                                                               parameters['release'],
                                                                               username,
                                                                               keycloak_roles,
                                                                               keycloak_default_roles)
        
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
        if settings.OIDC_VERIFY_SSL == False:
            gatekeeper['gatekeeper']['skip_tls'] = True
        parameters.update(gatekeeper)


        # For backwards-compatibility with old ingress spec:
        print("Ingress v1beta1: {}".format(settings.INGRESS_V1BETA1))
        ingress = {
            "ingress": {
                "v1beta1": settings.INGRESS_V1BETA1
            }
        }


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
        post_create_hooks(instance)


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
        post_delete_hooks(appinstance)
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
@transaction.atomic
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
    # TODO: Handle case of having many pods (could have many replicas, or could be right after update)
    for item in res_json['items']:
        release = item['metadata']['labels']['release']
        phase = item['status']['phase']
        
        deletion_timestamp = []
        if 'deletionTimestamp' in item['metadata']:
            deletion_timestamp = item['metadata']['deletionTimestamp']
            phase = "Terminated"
        num_containers = len(item['status']['containerStatuses'])
        num_cont_ready = 0
        if 'containerStatuses' in item['status']:
            for container in item['status']['containerStatuses']:
                if container['ready']:
                    num_cont_ready += 1
        if phase=="Running" and num_cont_ready != num_containers:
            phase = "Waiting"
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
                # if app_statuses[release]['deletion_status']:
                #     status.status_type = "Terminated"
                # else:
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
        try:
            appinstance = AppInstance.objects.get(parameters__contains={"release": entry['labels']['release']})
            # print(timestamp)
            # print(appinstance)
            # print(entry)
            datapoint = ResourceData(appinstance=appinstance, cpu=entry['cpu'], mem=entry['memory'], gpu=entry['gpu'], time=timestamp)
            datapoint.save()
        except:
            print("Didn't find corresponding AppInstance: {}".format(key))

    # print(timestamp)
    # print(json.dumps(resources, indent=2))  


@app.task
def sync_mlflow_models():
    mlflow_apps = AppInstance.objects.filter(~Q(state="Deleted"), project__status="active", app__slug="mlflow")
    for mlflow_app in mlflow_apps:

        current_time = time.time()-600
        url = 'http://{}:5000/{}'.format(mlflow_app.parameters['release'], 'api/2.0/preview/mlflow/model-versions/search')
        res = False
        try:
            res = requests.get(url)
        except Exception as err:
            print("Call to MLFlow Server failed.")
            print(err, flush=True)
        
        if res:
            models = res.json()
            for item in models['model_versions']:
                # print(item)
                name = item['name']
                version = 'v{}.0.0'.format(item['version'])
                release = 'major'
                source = item['source'].replace('s3://', '').split('/')
                bucket = source[0]
                experiment_id = source[1]
                run_id = source[2]
                path = '/'.join(source[1:])
                project = mlflow_app.project
                uid = run_id
                s3 = S3.objects.get(pk=mlflow_app.parameters['s3']['pk'])
                model_found = True
                try:
                    stackn_model = Model.objects.get(uid=uid)
                except:
                    model_found = False
                if not model_found:
                    model = Model(version=version, project=project, name=name, uid=uid, release_type=release, s3=s3, bucket="mlflow", path=path)
                    model.save()
                    obj_type = ObjectType.objects.filter(slug='mlflow-model')
                    model.object_type.set(obj_type)
                else:
                    if item['current_stage'] == 'Archived' and stackn_model.status != "AR":
                        stackn_model.status = "AR"
                        stackn_model.save()
                    if item['current_stage'] != 'Archived' and stackn_model.status == "AR":
                        stackn_model.status = "CR"
                        stackn_model.save()
        else:
            print("WARNING: Failed to fetch info from MLflow Server: {}".format(url))

@app.task
def clean_resource_usage():

    curr_timestamp = time.time()
    ResourceData.objects.filter(time__lte=curr_timestamp-48*3600).delete()

@app.task
def remove_deleted_app_instances():
    AppInstance.objects.filter(state="Deleted").delete()

@app.task
def clear_table_field():
    all_apps = AppInstance.objects.all()
    for app in all_apps:
        app.table_field = "{}"
        app.save()

    all_apps = Apps.objects.all()
    for app in all_apps:
        app.table_field = "{}"
        app.save()