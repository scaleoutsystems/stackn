from django.conf import settings

job_template = '''apiVersion: batch/v1
kind: Job
metadata:
  name: {name}-{id}
  namespace: {namespace}
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: kaniko
        image: gcr.io/kaniko-project/executor:latest
        env:
          - name: DOCKER_CONFIG
            value: "/kaniko/.docker/"
        args:
          - "--dockerfile=Dockerfile"
          - "--context=/workspace/"
          - "--destination={image}"
        volumeMounts:
          - name: git-source
            mountPath: /workspace
          - name: dockerjson
            mountPath: /kaniko/.docker/
            #subPath: config.json
          - name: dockerfile
            mountPath: /workspace/Dockerfile
            subPath: Dockerfile
      initContainers:
      - name: git-sync
        image: k8s.gcr.io/git-sync:v3.1.1
        args:
          - "-repo=https://github.com/leanaiorg/examples.git" 
          - "-dest=work"
        env:
          - name: GIT_SYNC_ONE_TIME
            value: "true"
        volumeMounts:
          - name: git-source
            mountPath: /tmp/git
        securityContext:
          runAsUser: 65533 # git-sync user
      volumes:
        - name: git-source
          emptyDir: {{}}
        - name: dockerjson
          secret:
            secretName: regcred
            items:
              - key: .dockerconfigjson
                path: config.json
        - name: dockerfile
          configMap:
            name: {name}-dockerfile'''


def load_definition(project):
    import yaml
    definition = __replace_vars(project, definition=job_template)
    __generate_and_apply_configmaps(project)
    ret = yaml.safe_load(definition)
    return ret


# TODO Refactor to also work for startup and teardown in addition to Dockerfile.
def __generate_and_apply_configmaps(project):
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    from pprint import pprint

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.CoreV1Api()

    try:
        api_response = api.delete_namespaced_config_map(
            namespace=settings.NAMESPACE,
            name="{}-dockerfile".format(project.name),
        )
        pprint(api_response)

    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_config_map: %s\n" % e)

    metadata = client.V1ObjectMeta(
        name="{}-dockerfile".format(project.name),
        namespace=settings.NAMESPACE,
    )
    # Instantiate the configmap object
    configmap = client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        # How do I modify here ?
        data=dict(Dockerfile=str(project.environment.dockerfile)),
        metadata=metadata
    )
    try:
        api_response = api.create_namespaced_config_map(
            namespace=settings.NAMESPACE,
            body=configmap,
            pretty='pretty_example',
        )
        pprint(api_response)

    except ApiException as e:
        print("Exception when calling CoreV1Api->create_namespaced_config_map: %s\n" % e)


def __replace_vars(project, definition):
    import uuid
    # TODO fetch from settings.
    url = 'registry.demo.scaleout.se'
    tag = 'latest'
    image = str(project.slug)
    project.image = url + '/' + image + ':' + tag
    new_def = str(definition).format(name=str(project.slug), image=project.image, namespace=settings.NAMESPACE,
                                     id=str(uuid.uuid4()))
    return new_def


def start_job(definition):
    print("deploying build baseimage job!".format())

    from kubernetes import client, config

    if settings.EXTERNAL_KUBECONF:
        config.load_kube_config('cluster.conf')
    else:
        config.load_incluster_config()

    api = client.BatchV1Api()

    # create the resource
    api.create_namespaced_job(
        namespace=settings.NAMESPACE,
        body=definition,
    )
    print("Resource created")
