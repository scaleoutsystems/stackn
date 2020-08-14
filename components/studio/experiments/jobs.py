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
      containers:
      - name: experiment
        image: python
        command: {command}
        volumeMounts:
        - name: jobstorage
          mountPath: /home/app/
      restartPolicy: Never
      volumes:
      - name: jobstorage
        persistentVolumeClaim:
          claimName: {name}-project-files
  backoffLimit: 4"""


# TODO make a generalized shared function between jobs, workflows and deployments.
def get_instance_from_definition(instance):
    import yaml

    ret = example.format(
        name=instance.project.slug,
        id=instance.id,
        command=str(instance.command.split(' ')),
        namespace=settings.NAMESPACE
    )
    ret = yaml.safe_load(ret)

    return ret


def run_job(instance):
    print("deploying job with {}!".format(instance))

    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.BatchV1Api()

    yaml_definition = get_instance_from_definition(instance)

    # create the resource
    api.create_namespaced_job(
        namespace=settings.NAMESPACE,
        body=yaml_definition,
    )
    print("Resource created")

    # get the resource and print out data
    print("getting logs:")
    resource = api.read_namespaced_job(
        name=str(instance.id),
        namespace=settings.NAMESPACE,
    )
    print("got logs?")
    # resource = api.list_namespaced_job(
    #   namespace="stack-fn",
    # )
    print("Resources details:")
    pprint(resource)


def delete_job(instance):
    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.BatchV1Api()

    api.delete_namespaced_job(
        name=str(instance.id),
        namespace=settings.NAMESPACE,
        body=client.V1DeleteOptions(),
    )
    print("Resource deleted")


def get_logs(experiment):
    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.BatchV1Api()

    ret = api.read_namespaced_job(
        name=str(experiment.id),
        namespace=settings.NAMESPACE,
    )
    print("getting job name:")
    job_name = ret.metadata.labels['job-name']

    api = client.CoreV1Api()
    ret = api.list_namespaced_pod(namespace=settings.NAMESPACE, label_selector='job-name={}'.format(job_name))

    ret = api.read_namespaced_pod_log(
        name=ret.items[0].metadata.name,
        namespace=settings.NAMESPACE)

    return ret
