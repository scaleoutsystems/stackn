from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.db.models import Q
from projects.helpers import get_minio_keys
from django.core import serializers
from .helpers import create_user_settings
from rest_framework.renderers import JSONRenderer
import uuid
import yaml
import json
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify
from deployments.models import HelmResource
from projects.models import Environment, Flavor
from projects.models import Project, ProjectLog, Volume
from clusters.models import Cluster
from modules import keycloak_lib as keylib
from rest_framework.serializers import ModelSerializer


class ProjectSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id', 'name', 'description', 'slug', 'owner', 'image', 'project_key', 'project_secret', 'updated_at',
            'created_at', 'repository', 'repository_imported')


class SessionManager(models.Manager):

    def generate_passkey(self, length=20):
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        return password

    def create_session(self, name, project, lab_session_owner, chart, settings, helm_repo=None):
        slug = slugify(name)
        key = self.generate_passkey()
        secret = self.generate_passkey(40)
        _sett = yaml.safe_dump(settings)
        status = 'CR'
        session = self.create(name=name,
                              project=project,
                              lab_session_owner=lab_session_owner,
                              status=status,
                              slug=slug,
                              session_key=key,
                              session_secret=secret,
                              chart=chart,
                              settings=_sett,
                              helm_repo=helm_repo)

        return session


class Session(models.Model):

    objects = SessionManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512, unique=False)
    slug = models.CharField(max_length=512)
    CREATED = 'CR'
    STARTED = 'ST'
    STOPPED = 'SP'
    FINISHED = 'FN'
    ABORTED = 'AB'
    STATUS = [
        (CREATED, 'Created'),
        (STARTED, 'Started'),
        (STARTED, 'Stopped'),
        (FINISHED, 'Finished'),
        (ABORTED, 'Aborted'),
    ]
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='session')
    lab_session_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lab_session_owner')

    helmchart = models.OneToOneField('deployments.HelmResource', on_delete=models.CASCADE)
    keycloak_client_id = models.CharField(max_length=512)
    appname = models.CharField(max_length=512)
    flavor_slug = models.CharField(max_length=512)
    environment_slug = models.CharField(max_length=512)

    helm_repo = models.CharField(max_length=1024, null=True, blank=True)

    status = models.CharField(max_length=2, choices=STATUS, default=CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

@receiver(pre_delete, sender=Session, dispatch_uid='session_pre_delete_signal')
def pre_delete_labs(sender, instance, using, **kwargs):
    kc = keylib.keycloak_init()
    keylib.keycloak_delete_client(kc, instance.keycloak_client_id)
    
    scope_id = keylib.keycloak_get_client_scope_id(kc, instance.keycloak_client_id+'-scope')
    keylib.keycloak_delete_client_scope(kc, scope_id)

    l = ProjectLog(project=instance.project, module='LA', headline='Lab Session',
                       description='Lab Session {name} has been removed'.format(name=instance.name))
    l.save()

@receiver(pre_save, sender=Session, dispatch_uid='session_pre_save_signal')
def pre_save_labs(sender, instance, using, **kwargs):

    instance.slug = slugify(instance.name)

    RELEASE_NAME = str(instance.slug)
    HOST = settings.DOMAIN
    

    URL = 'https://'+RELEASE_NAME+'.'+HOST
    global_domain = settings.DOMAIN
    namespace = settings.NAMESPACE

    cluster_name = instance.project.cluster
    cluster = Cluster.objects.get(name=cluster_name)
    namespace = cluster.namespace
    global_domain = cluster.base_url
    URL = 'https://'+RELEASE_NAME+'.'+cluster.base_url
    # if hasattr(instance, "cluster"):
    #     try:
    #         print("CLUSTER")
    #         print(instance.cluster)
    #         cluster = Cluster.objects.filter(name=instance.cluster).first()
    #         print(cluster)
    #         URL = 'https://'+RELEASE_NAME+'.'+cluster.base_url
    #         print(URL)
    #         global_domain = cluster.base_url
    #         print(global_domain)
    #         namespace = cluster.namespace
    #         print(namespace)
    #         cluster_name = cluster.name
    #         print(cluster.name)
    #     except:
    #         cluster = []
    #         print('In labs: Using default cluster (this).')
        

    user = instance.lab_session_owner.username
    client_id, client_secret = keylib.keycloak_setup_base_client(URL, RELEASE_NAME, user, ['owner'], ['owner'])
    
    instance.keycloak_client_id = client_id
    instance.appname = '{}-{}-lab'.format(instance.slug, instance.project.slug)
    skip_tls = 0
    if not settings.OIDC_VERIFY_SSL:
        skip_tls = 1
        print("WARNING: Skipping TLS verify.")

    volume_param = []
    if hasattr(instance, "extraVols") and instance.extraVols:
        vols = instance.extraVols.split(',')
        extraVolumes = ""
        extraVolumeMounts = ""
        i = 1
        print("VOLS")
        print(vols)
        for vol in vols:
            try:
                volobject = Volume.objects.get(name=vol, project_slug=instance.project.slug)
                print(volobject)
                volume_name = 'extravol'+str(i)
                extraVolumes += """
- name: {}
  persistentVolumeClaim:
    claimName: {}
                """.format(volume_name, volobject.slug)

                extraVolumeMounts += """
- name: {}
  mountPath: /home/jovyan/{}
                """.format(volume_name, vol)
                i = i+1
            except:
                pass
        if i>1:
            volume_param = {"extraVolumes": extraVolumes, "extraVolumeMounts": extraVolumeMounts}
    print(volume_param)
    parameters = {'release': RELEASE_NAME,
                  'chart': 'lab',
                  'global.domain': global_domain,
                  'project.name': instance.project.slug,
                  'appname': instance.appname,
                  'gatekeeper.realm': settings.KC_REALM,
                  'gatekeeper.client_secret': client_secret,
                  'gatekeeper.client_id': client_id,
                  'gatekeeper.auth_endpoint': settings.OIDC_OP_REALM_AUTH,
                  'gatekeeper.skip_tls': str(skip_tls)
                  }
    if volume_param:
        parameters.update(volume_param)
    ingress_secret_name = 'prod-ingress'
    try:
        ingress_secret_name = settings.LABS['ingress']['secretName']
    except:
        pass
    
    project = instance.project
    minio_keys = get_minio_keys(project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']

    settings_file = ProjectSerializer(project)

    settings_file = JSONRenderer().render(settings_file.data)
    settings_file = settings_file.decode('utf-8')

    settings_file = json.loads(settings_file)
    settings_file = yaml.dump(settings_file)

    user_config_file = create_user_settings(user)
    user_config_file = yaml.dump(json.loads(user_config_file))

    flavor = Flavor.objects.filter(slug=instance.flavor_slug).first()
    environment = Environment.objects.filter(slug=instance.environment_slug).first()

    prefs = {'namespace': namespace,
              'labs.resources.requests.cpu': str(flavor.cpu),
              'labs.resources.limits.cpu': str(flavor.cpu),
              'labs.resources.requests.memory': str(flavor.mem),
              'labs.resources.limits.memory': str(flavor.mem),
              'labs.resources.requests.gpu': str(flavor.gpu),
              'labs.resources.limits.gpu': str(flavor.gpu),
              'labs.gpu.enabled': str("true" if flavor.gpu else "false"),
              'labs.image': environment.image,
              'ingress.secretName': ingress_secret_name,
              'minio.access_key': decrypted_key,
              'minio.secret_key': decrypted_secret,
              'settings_file': settings_file,
              'user_settings_file': user_config_file,
              'project.slug': project.slug
              }
    
    parameters.update(prefs)
    print(parameters)
    helmchart = HelmResource(name=RELEASE_NAME,
                             namespace=namespace,
                             chart='lab',
                             params=parameters,
                             username=user,
                             cluster=cluster_name)
    helmchart.save()
    instance.helmchart = helmchart

    l = ProjectLog(project=project, module='LA', headline='Lab Session',
                               description='A new Lab Session {name} has been created'.format(name=RELEASE_NAME))
    l.save()