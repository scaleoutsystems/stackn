from django.db import models
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_delete, pre_save
from django.conf import settings
from deployments.models import HelmResource
from models.models import Model
from projects.models import Project, Volume
from projects.helpers import get_minio_keys
from django.contrib.auth.models import User
from modules import keycloak_lib as keylib
import uuid


class AppCategories(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, default="")
    def __str__(self):
        return str(self.name)

class Apps(models.Model):
    name = models.CharField(max_length=512)
    slug = models.CharField(max_length=512, blank=True, null=True)
    category = models.ForeignKey('AppCategories', related_name="apps", on_delete=models.CASCADE, null=True)
    description = models.TextField(blank=True, null=True, default="")
    settings = models.TextField(blank=True, null=True)
    exposed = models.CharField(max_length=10, default="external")
    schema = models.CharField(max_length=10, default="https://")
    port = models.CharField(max_length=10, default="", null=True)
    path = models.CharField(max_length=512, blank=True, default="", null=True)
    chart = models.CharField(max_length=512)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class AppInstance(models.Model):
    # TODO: Name, project should be unique combination
    name = models.CharField(max_length=512, default="app_name")
    app = models.ForeignKey('Apps', on_delete=models.CASCADE, related_name='appinstance')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='appinstance')
    helmchart = models.OneToOneField('deployments.HelmResource', on_delete=models.CASCADE, null=True)
    app_dependencies = models.ManyToManyField('apps.AppInstance')
    vol_dependencies = models.ManyToManyField('projects.Volume')
    model_dependencies = models.ManyToManyField('models.Model')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_owner', null=True)
    url = models.CharField(max_length=512, null=True)
    info = models.TextField(blank=True, null=True)
    settings = models.TextField(blank=True, null=True)
    parameters = models.TextField(blank=True, null=True)
    keycloak_client_id = models.CharField(max_length=512, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


@receiver(pre_save, sender=AppInstance, dispatch_uid='appinstance_pre_save_signal')
def pre_save_apps(sender, instance, using, **kwargs):

    # instance_settings = eval(instance.settings)
    if instance.action == "create":
        RELEASE_NAME = instance.app.slug+'-'+instance.project.slug+'-'+uuid.uuid4().hex[0:4]
    else:
        RELEASE_NAME = instance.helmchart.name


    SERVICE_NAME = RELEASE_NAME
    # TODO: Fix for multicluster setup, look at e.g. labs
    HOST = settings.DOMAIN
    NAMESPACE = settings.NAMESPACE

    if instance.app.exposed == 'external':
        URL = instance.app.schema+RELEASE_NAME+'.'+HOST
        KC_URL = URL
    elif instance.app.exposed == 'internal':
        URL = instance.app.schema+RELEASE_NAME
        KC_URL = 'http://dummy.com'
    else:
        URL = ''
        KC_URL = 'http://dummy.com'
    user = instance.owner

    if instance.action == "create":
        client_id, client_secret = keylib.keycloak_setup_base_client(KC_URL, RELEASE_NAME, str(user), ['owner'], ['owner'])
        instance.keycloak_client_id = client_id
    else:
        existing_params = eval(instance.helmchart.params)
        client_id = existing_params['gatekeeper.client_id']
        client_secret = existing_params['gatekeeper.client_secret']

    skip_tls = 0
    if not settings.OIDC_VERIFY_SSL:
        skip_tls = 1
        print("WARNING: Skipping TLS verify.")




    parameters = {
        "release": RELEASE_NAME,
        "chart": str(instance.app.chart),
        "namespace": NAMESPACE,
        "appname": RELEASE_NAME,
        "project.name": instance.project.name,
        "project.slug": instance.project.slug,
        "app.resources.requests.memory": "250Mi",
        "app.resources.requests.cpu": "0.1",
        "app.resources.limits.memory": "4Gi",
        "app.resources.limits.cpu": "2.0",
        "gpu.enabled": "false",
        "global.domain": HOST,
        'gatekeeper.realm': settings.KC_REALM,
        'gatekeeper.client_secret': client_secret,
        'gatekeeper.client_id': client_id,
        'gatekeeper.auth_endpoint': settings.OIDC_OP_REALM_AUTH,
        'gatekeeper.skip_tls': str(skip_tls),
        's3sync.image': "scaleoutsystems/s3-sync:latest",
        'service.name': SERVICE_NAME,
        'storageClass': settings.STORAGECLASS
    }


    parameters.update(eval(instance.parameters))

    if instance.action == "create":
        helmchart = HelmResource(name=RELEASE_NAME,
                                namespace=settings.NAMESPACE,
                                chart=instance.app.chart,
                                params=parameters,
                                username=str(user))


        helmchart.save()
        instance.helmchart = helmchart

    elif instance.action == "update":
        helmchart = instance.helmchart
        helmchart.params = parameters
        helmchart.save()
    else:
        raise Exception("Incorrect action on app.")
    
    instance.url = URL.strip('/')+'/'
    if instance.app.path:
        instance.url += str(instance.app.path)
    if instance.app.port and instance.app.port != '' and int(instance.app.port) > 0:
        instance.url = instance.url.strip('/')+':'+str(instance.app.port)
    info = {"status": "OK", "release": str(RELEASE_NAME)}
    instance.info = str(info)

@receiver(pre_delete, sender=AppInstance, dispatch_uid='appinstance_pre_delete_signal')
def pre_delete_appinstance(sender, instance, using, **kwargs):
    try:
        kc = keylib.keycloak_init()
        keylib.keycloak_delete_client(kc, instance.keycloak_client_id)
        
        scope_id = keylib.keycloak_get_client_scope_id(kc, instance.keycloak_client_id+'-scope')
        keylib.keycloak_delete_client_scope(kc, scope_id)
    except Exception as err:
        print("Failed to delete keycloak client and client scope.")
        print(err)
