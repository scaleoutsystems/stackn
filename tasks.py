import json
import subprocess
import time
from datetime import datetime

import requests
from celery import shared_task
from django.conf import settings
from django.core.exceptions import EmptyResultSet
from django.db import transaction
from django.db.models import Q
from models.models import Model, ObjectType
from projects.models import S3, BasicAuth, Environment, MLFlow

from studio.celery import app

from . import controller
from .models import AppInstance, Apps, AppStatus, ResourceData


def get_URI(parameters):
    URI = (
        "https://"
        + parameters["release"]
        + "."
        + parameters["global"]["domain"]
    )

    URI = URI.strip("/")
    return URI


def process_helm_result(results):
    stdout = results.stdout.decode("utf-8")
    stderr = results.stderr.decode("utf-8")
    return stdout, stderr


def post_create_hooks(instance):
    print("TASK - POST CREATE HOOK...")
    # hard coded hooks for now, we can make this dynamic
    # and loaded from the app specs
    if instance.app.slug == "minio":
        # Create project S3 object
        # TODO: If the instance is being updated,
        # update the existing S3 object.
        access_key = instance.parameters["credentials"]["access_key"]
        secret_key = instance.parameters["credentials"]["secret_key"]

        # OBS!! TEMP WORKAROUND to be able to connect to minio
        minio_svc = "{}-minio".format(instance.parameters["release"])
        cmd = (
            "kubectl"
            + " get svc "
            + minio_svc
            + ' -o jsonpath="{.spec.clusterIP"}'
        )
        minio_host_url = ""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            minio_host_url = result.stdout.decode("utf-8")
            minio_host_url += ":9000"
        except subprocess.CalledProcessError:
            print(
                "Oops, something went wrong running the command: {}".format(
                    cmd
                )
            )

        try:
            s3obj = instance.s3obj
            s3obj.access_key = access_key
            s3obj.secret_key = secret_key
            s3obj.host = minio_host_url
        except:  # noqa E722 TODO: Add exception
            s3obj = S3(
                name=instance.name,
                project=instance.project,
                host=minio_host_url,
                access_key=access_key,
                secret_key=secret_key,
                app=instance,
                owner=instance.owner,
            )
        s3obj.save()

    if instance.app.slug == "environment":
        params = instance.parameters
        image = params["container"]["name"]
        # We can assume one registry here
        for reg_key in params["apps"]["docker_registry"].keys():
            reg_release = params["apps"]["docker_registry"][reg_key]["release"]
            reg_domain = params["apps"]["docker_registry"][reg_key]["global"][
                "domain"
            ]
        repository = reg_release + "." + reg_domain
        registry = AppInstance.objects.get(
            parameters__contains={"release": reg_release}
        )

        target_environment = Environment.objects.get(
            pk=params["environment"]["pk"]
        )
        target_app = target_environment.app

        env_obj = Environment(
            name=instance.name,
            project=instance.project,
            repository=repository,
            image=image,
            registry=registry,
            app=target_app,
            appenv=instance,
        )
        env_obj.save()

    if instance.app.slug == "mlflow":
        params = instance.parameters

        # OBS!! TEMP WORKAROUND to be able to connect to mlflow (internal dns
        # between docker and k8s does not work currently)
        # Sure one could use FQDN but lets avoid going via the internet
        mlflow_svc = instance.parameters["service"]["name"]
        cmd = (
            "kubectl"
            + " get svc "
            + mlflow_svc
            + ' -o jsonpath="{.spec.clusterIP"}'
        )
        mlflow_host_ip = ""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            mlflow_host_ip = result.stdout.decode("utf-8")
            mlflow_host_ip += ":{}".format(
                instance.parameters["service"]["port"]
            )
        except subprocess.CalledProcessError:
            print(
                "Oops, something went wrong running the command: {}".format(
                    cmd
                )
            )

        s3 = S3.objects.get(pk=instance.parameters["s3"]["pk"])
        basic_auth = BasicAuth(
            owner=instance.owner,
            name=instance.name,
            project=instance.project,
            username=instance.parameters["credentials"]["username"],
            password=instance.parameters["credentials"]["password"],
        )
        basic_auth.save()
        obj = MLFlow(
            name=instance.name,
            project=instance.project,
            mlflow_url="https://{}.{}".format(
                instance.parameters["release"],
                instance.parameters["global"]["domain"],
            ),
            s3=s3,
            host=mlflow_host_ip,
            basic_auth=basic_auth,
            app=instance,
            owner=instance.owner,
        )
        obj.save()


def release_name(instance):
    # Free up release name (if reserved)
    rel_names = instance.releasename_set.all()

    for rel_name in rel_names:
        rel_name.status = "active"
        rel_name.app = None
        rel_name.save()


def post_delete_hooks(instance):
    print("TASK - POST DELETE HOOK...")
    release_name(instance)
    project = instance.project
    if project.s3storage and project.s3storage.app == instance:
        project.s3storage.delete()
    elif project.mlflow and project.mlflow.app == instance:
        project.mlflow.delete()


@shared_task
@transaction.atomic
def deploy_resource(instance_pk, action="create"):
    print("TASK - DEPLOY RESOURCE...")
    app_instance = AppInstance.objects.select_for_update().get(pk=instance_pk)
    status = AppStatus(appinstance=app_instance)

    if action == "create":

        parameters = app_instance.parameters
        status.status_type = "Created"
        status.info = parameters["release"]

        # For backwards-compatibility with old ingress spec:
        if "ingress" not in parameters:
            parameters["ingress"] = dict()
        try:
            print("Ingress v1beta1: {}".format(settings.INGRESS_V1BETA1))
            parameters["ingress"]["v1beta1"] = settings.INGRESS_V1BETA1
        except:  # noqa E722 TODO: Add exception
            pass

        app_instance.parameters = parameters
        print("App Instance paramenters: {}".format(app_instance))
        app_instance.save()

    results = controller.deploy(app_instance.parameters)
    stdout, stderr = process_helm_result(results)

    if results.returncode == 0:
        print("Helm install succeeded")
        status.status_type = "Installed"
        app_instance.state = "Running"
        helm_info = {
            "success": True,
            "info": {"stdout": stdout, "stderr": stderr},
        }
    else:
        print("Helm install failed")
        status.status_type = "Failed"
        app_instance.state = "Failed"
        helm_info = {
            "success": False,
            "info": {"stdout": stdout, "stderr": stderr},
        }

    app_instance.info["helm"] = helm_info
    app_instance.save()
    status.save()

    if results.returncode != 0:
        print(app_instance.info["helm"])
    else:
        post_create_hooks(app_instance)


@shared_task
@transaction.atomic
def delete_resource(pk):
    appinstance = AppInstance.objects.select_for_update().get(pk=pk)

    if appinstance and appinstance.state != "Deleted":
        # The instance does exist.
        parameters = appinstance.parameters
        # TODO: Check that the user has the permission required to delete it.

        # TODO: Fix for multicluster setup
        # TODO: We are assuming this URI here, but we should allow
        # for other forms.
        # The instance should store information about this.

        # Invoke chart controller
        results = controller.delete(parameters)

        if (
            results.returncode == 0
            or "release: not found" in results.stderr.decode("utf-8")
        ):
            status = AppStatus(appinstance=appinstance)
            status.status_type = "Terminated"
            status.save()
            print("CALLING POST DELETE HOOKS")
            post_delete_hooks(appinstance)
        else:
            status = AppStatus(appinstance=appinstance)
            status.status_type = "FailedToDelete"
            status.save()
            appinstance.state = "FailedToDelete"


@shared_task
@transaction.atomic
def delete_resource_permanently(appinstance):

    parameters = appinstance.parameters

    # Invoke chart controller
    results = controller.delete(parameters)

    if not (
        results.returncode == 0
        or "release: not found" in results.stderr.decode("utf-8")
    ):
        status = AppStatus(appinstance=appinstance)
        status.status_type = "FailedToDelete"
        status.save()
        appinstance.state = "FailedToDelete"

    release_name(appinstance)

    appinstance.delete()


@app.task
@transaction.atomic
def check_status():
    # TODO: Fix for multicluster setup.
    args = [
        "kubectl",
        "-n",
        settings.NAMESPACE,
        "get",
        "po",
        "-l",
        "type=app",
        "-o",
        "json",
    ]
    # print(args)
    results = subprocess.run(args, capture_output=True)
    # print(results)
    res_json = json.loads(results.stdout.decode("utf-8"))
    app_statuses = dict()
    # print(res_json)
    # TODO: Handle case of having many pods (could have many replicas,
    # or could be right after update)
    for item in res_json["items"]:
        release = item["metadata"]["labels"]["release"]
        phase = item["status"]["phase"]

        deletion_timestamp = []
        if "deletionTimestamp" in item["metadata"]:
            deletion_timestamp = item["metadata"]["deletionTimestamp"]
            phase = "Terminated"
        num_containers = -1
        try:
            num_containers = len(item["status"]["containerStatuses"])
        except:  # noqa E722 TODO: Add exception
            print("Failed to get number of containers.")
            pass
        num_cont_ready = 0
        if "containerStatuses" in item["status"]:
            for container in item["status"]["containerStatuses"]:
                if container["ready"]:
                    num_cont_ready += 1
        if phase == "Running" and num_cont_ready != num_containers:
            phase = "Waiting"
        app_statuses[release] = {
            "phase": phase,
            "num_cont": num_containers,
            "num_cont_ready": num_cont_ready,
            "deletion_status": deletion_timestamp,
        }

    # Fetch all app instances whose state is not "Deleted"
    instances = AppInstance.objects.filter(~Q(state="Deleted"))

    for instance in instances:
        release = instance.parameters["release"]
        if release in app_statuses:
            current_status = app_statuses[release]["phase"]
            try:
                latest_status = (
                    AppStatus.objects.filter(appinstance=instance)
                    .latest("time")
                    .status_type
                )
            except:  # noqa E722 TODO: Add exception
                latest_status = "Unknown"
            if current_status != latest_status:
                print("New status for release {}".format(release))
                print("Current status: {}".format(current_status))
                print("Previous status: {}".format(latest_status))
                status = AppStatus(appinstance=instance)
                # if app_statuses[release]['deletion_status']:
                #     status.status_type = "Terminated"
                # else:
                status.status_type = app_statuses[release]["phase"]
                # status.info = app_statuses[release]
                status.save()
            # else:
            #     print("No update for release: {}".format(release))
        else:
            delete_exists = AppStatus.objects.filter(
                appinstance=instance, status_type="Terminated"
            ).exists()
            if delete_exists:
                status = AppStatus(appinstance=instance)
                status.status_type = "Deleted"
                status.save()
                instance.state = "Deleted"
                instance.deleted_on = datetime.now()
                instance.save()

    # Fetch all app instances whose state is "Deleted" and check whether
    # there are related pods which are still running
    pod_status = "None"
    instances = AppInstance.objects.filter(state="Deleted")
    for instance in instances:
        if "url" in instance.table_field:
            # Find the app instance release name
            app_release = instance.parameters["release"]  # e.g 'rfc058c6f'
            # Now check if there exists a pod with that release
            cmd = "kubectl" + " get po -l release=" + app_release
            try:
                # returns a byte-like object
                result = subprocess.run(cmd, shell=True, capture_output=True)
                result_stdout = result.stdout.decode("utf-8")
                result_stderr = result.stderr.decode("utf-8")
            except subprocess.CalledProcessError:
                print("Error running the command: {}".format(cmd))

            if (
                result_stdout != ""
                and "No resources found in default namespace."
                not in result_stderr
            ):
                # Extract the the status of the related release pod
                cmd = (
                    "kubectl"
                    + " get po -l release="
                    + app_release
                    + ' -o jsonpath="{.items[0].status.phase}"'
                )
                try:
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True
                    )
                    pod_status = result.stdout.decode("utf-8")
                    print(pod_status)
                except subprocess.CalledProcessError:
                    print("Error running the command: {}".format(cmd))

                if pod_status == "Running" and instance.state == "Deleted":
                    print("INFO: running pod associated to app (Deleted)")
                    print(
                        "INFO: DELETE RESOURCE with release: {}".format(
                            app_release
                        )
                    )
                    cmd = "helm" + " delete " + app_release
                    try:
                        result = subprocess.run(
                            cmd, shell=True, capture_output=True
                        )
                        print(result)
                    except subprocess.CalledProcessError:
                        print("Error running the command: {}".format(cmd))


@app.task
def get_resource_usage():

    timestamp = time.time()

    args = ["kubectl", "get", "--raw", "/apis/metrics.k8s.io/v1beta1/pods"]
    results = subprocess.run(args, capture_output=True)

    pods = []
    try:
        res_json = json.loads(results.stdout.decode("utf-8"))
        pods = res_json["items"]
    except:  # noqa E722 TODO: Add exception
        pass

    resources = dict()

    args_pod = ["kubectl", "get", "po", "-o", "json"]
    results_pod = subprocess.run(args_pod, capture_output=True)
    results_pod_json = json.loads(results_pod.stdout.decode("utf-8"))
    try:
        for pod in results_pod_json["items"]:
            if (
                "metadata" in pod
                and "labels" in pod["metadata"]
                and "release" in pod["metadata"]["labels"]
                and "project" in pod["metadata"]["labels"]
            ):
                pod_name = pod["metadata"]["name"]
                resources[pod_name] = dict()
                resources[pod_name]["labels"] = pod["metadata"]["labels"]
                resources[pod_name]["cpu"] = 0.0
                resources[pod_name]["memory"] = 0.0
                resources[pod_name]["gpu"] = 0
    except:  # noqa E722 TODO: Add exception
        pass

    try:
        for pod in pods:

            podname = pod["metadata"]["name"]
            if podname in resources:
                containers = pod["containers"]
                cpu = 0
                mem = 0
                for container in containers:
                    cpun = container["usage"]["cpu"]
                    memki = container["usage"]["memory"]
                    try:
                        cpu += int(cpun.replace("n", "")) / 1e6
                    except:  # noqa E722 TODO: Add exception
                        print("Failed to parse CPU usage:")
                        print(cpun)
                    if "Ki" in memki:
                        mem += int(memki.replace("Ki", "")) / 1000
                    elif "Mi" in memki:
                        mem += int(memki.replace("Mi", ""))
                    elif "Gi" in memki:
                        mem += int(memki.replace("Mi", "")) * 1000

                resources[podname]["cpu"] = cpu
                resources[podname]["memory"] = mem
    except:  # noqa E722 TODO: Add exception
        pass
    # print(json.dumps(resources, indent=2))

    for key in resources.keys():
        entry = resources[key]
        # print(entry['labels']['release'])
        try:
            appinstance = AppInstance.objects.get(
                parameters__contains={"release": entry["labels"]["release"]}
            )
            # print(timestamp)
            # print(appinstance)
            # print(entry)
            datapoint = ResourceData(
                appinstance=appinstance,
                cpu=entry["cpu"],
                mem=entry["memory"],
                gpu=entry["gpu"],
                time=timestamp,
            )
            datapoint.save()
        except:  # noqa E722 TODO: Add exception
            print("Didn't find corresponding AppInstance: {}".format(key))

    # print(timestamp)
    # print(json.dumps(resources, indent=2))


@app.task
def sync_mlflow_models():
    mlflow_apps = AppInstance.objects.filter(
        ~Q(state="Deleted"), project__status="active", app__slug="mlflow"
    )
    for mlflow_app in mlflow_apps:

        url = "http://{}/{}".format(
            mlflow_app.project.mlflow.host,
            "api/2.0/preview/mlflow/model-versions/search",
        )
        res = False
        try:
            res = requests.get(url)
        except Exception as err:
            print("Call to MLFlow Server failed.")
            print(err, flush=True)

        if res:
            models = res.json()
            print(models)
            if len(models) > 0:
                for item in models["model_versions"]:
                    # print(item)
                    name = item["name"]
                    version = "v{}.0.0".format(item["version"])
                    release = "major"
                    source = item["source"].replace("s3://", "").split("/")
                    run_id = source[2]
                    path = "/".join(source[1:])
                    project = mlflow_app.project
                    uid = run_id
                    s3 = S3.objects.get(pk=mlflow_app.parameters["s3"]["pk"])
                    model_found = True
                    try:
                        stackn_model = Model.objects.get(uid=uid)
                    except:  # noqa E722 TODO: Add exception
                        model_found = False
                    if not model_found:
                        obj_type = ObjectType.objects.filter(slug="mlflow")
                        if obj_type.exists():
                            model = Model(
                                version=version,
                                project=project,
                                name=name,
                                uid=uid,
                                release_type=release,
                                s3=s3,
                                bucket="mlflow",
                                path=path,
                            )
                            model.save()
                            model.object_type.set(obj_type)
                        else:
                            raise EmptyResultSet
                    else:
                        if (
                            item["current_stage"] == "Archived"
                            and stackn_model.status != "AR"
                        ):
                            stackn_model.status = "AR"
                            stackn_model.save()
                        if (
                            item["current_stage"] != "Archived"
                            and stackn_model.status == "AR"
                        ):
                            stackn_model.status = "CR"
                            stackn_model.save()
        else:
            print(
                "WARNING: Failed to fetch info from MLflow Server: {}".format(
                    url
                )
            )


@app.task
def clean_resource_usage():

    curr_timestamp = time.time()
    ResourceData.objects.filter(time__lte=curr_timestamp - 48 * 3600).delete()


@app.task
def remove_deleted_app_instances():
    apps = AppInstance.objects.filter(state="Deleted")
    print("NUMBER OF APPS TO DELETE: {}".format(len(apps)))
    for instance in apps:
        try:
            name = instance.name
            print("Deleting app instance: {}".format(name))
            instance.delete()
            print("Deleted app instance: {}".format(name))
        except Exception as err:
            print("Failed to delete app instances.")
            print(err)


@app.task
def clear_table_field():
    all_apps = AppInstance.objects.all()
    for instance in all_apps:
        instance.table_field = "{}"
        instance.save()

    all_apps = Apps.objects.all()
    for instance in all_apps:
        instance.table_field = "{}"
        instance.save()


@app.task
def purge_tasks():
    """
    Remove tasks from queue to avoid overflow
    """
    app.control.purge()
