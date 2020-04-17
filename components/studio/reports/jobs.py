from django.conf import settings
from pprint import pprint

example = """apiVersion: batch/v1
kind: Job
metadata:
  name: {id}
  namespace: {namespace}
spec:
  template:
    spec:
      imagePullSecrets:
      - name: regcred
      containers:
      - name: report-generator
        image: registry.demo.scaleout.se/testar:latest
        command: ["python", "{path_to_file}", "{model_uid}"]
        volumeMounts:
        - name: jobstorage
          mountPath: /home/jovyan/
      restartPolicy: Never
      volumes:
      - name: jobstorage
        persistentVolumeClaim:
          claimName: {name}-project-files
  backoffLimit: 1"""


def get_instance_from_definition(instance):
    import yaml

    result = example.format(
        id=instance['id'],
        namespace=settings.NAMESPACE,
        path_to_file=instance['path_to_file'],
        model_uid=instance['model_uid'],
        name=instance['project_name']
    )

    return yaml.safe_load(result)


def run_job(instance):
    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.BatchV1Api()

    yaml_definition = get_instance_from_definition(instance)

    api.create_namespaced_job(
        namespace=settings.NAMESPACE,
        body=yaml_definition
    )

    resource = api.read_namespaced_job(
        name=instance['id'],
        namespace=settings.NAMESPACE
    )

    pprint(resource)


def delete_job(instance):
    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.BatchV1Api()

    api.delete_namespaced_job(
        name=instance['id'],
        namespace=settings.NAMESPACE,
        body=client.V1DeleteOptions()
    )


def get_logs(job_id):
    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.BatchV1Api()
    result = api.read_namespaced_job(
        name=job_id,
        namespace=settings.NAMESPACE
    )
    job_name = result.metadata.labels['job-name']

    api = client.CoreV1Api()
    result = api.list_namespaced_pod(
        namespace=settings.NAMESPACE,
        label_selector='job-name={}'.format(job_name)
    )
    result = api.read_namespaced_pod_log(
        name=result.items[0].metadata.name,
        namespace=settings.NAMESPACE
    )

    return result
