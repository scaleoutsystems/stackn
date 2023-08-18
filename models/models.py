from functools import cmp_to_key

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils.module_loading import import_string
from minio import Minio
from tagulous.models import TagField


def compare_version(v1, v2):
    VERSION_CLASS = import_string(settings.VERSION_BACKEND)
    v1obj = VERSION_CLASS(v1.version)
    v2obj = VERSION_CLASS(v2.version)
    if v1obj < v2obj:
        return -1
    elif v1obj > v2obj:
        return 1
    else:
        return 0


class ModelManager(models.Manager):
    def sorted_by_version(self, model_name, project):
        models = super().get_queryset().filter(project=project, name=model_name)
        if models:
            models = sorted(models, key=cmp_to_key(compare_version))
            return models
        return []

    # Get latest version.
    def latest(self, model_name, project):
        # Get all models in the project
        models = super().get_queryset().filter(project=project, name=model_name)
        if models:
            # Sort by version
            models = sorted(models, key=cmp_to_key(compare_version))
            for model in models:
                print("{}-{}".format(model.name, model.version))
            return models[0]

        return []


class ObjectType(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, default="Model")
    slug = models.CharField(max_length=100, null=True, blank=True, default="model")
    app_slug = models.CharField(max_length=100, null=True, blank=True)

    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


def upload_headline_path(instance, filename):
    return "models/model_{0}/{1}".format(instance.pk, filename)


class Model(models.Model):
    objects_version = ModelManager()
    objects = models.Manager()
    PRIVATE = "PR"
    LIMITED = "LI"
    PUBLIC = "PU"
    ACCESS = [
        (PRIVATE, "Private"),
        (LIMITED, "Limited"),
        (PUBLIC, "Public"),
    ]

    CREATED = "CR"
    DEPLOYED = "DP"
    ARCHIVED = "AR"
    STATUS = [
        (CREATED, "Created"),
        (DEPLOYED, "Deployed"),
        (ARCHIVED, "Archived"),
    ]

    MAJOR = "M"
    MINOR = "m"
    RELEASE_TYPE = [
        (MAJOR, "Major"),
        (MINOR, "Minor"),
    ]
    uid = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=255, default="1.0")
    release_type = models.CharField(max_length=255, choices=RELEASE_TYPE, default=MINOR)
    description = models.CharField(max_length=255, null=True, blank=True)
    model_card = models.TextField(null=True, blank=True)
    access = models.CharField(max_length=2, choices=ACCESS, default=PRIVATE)
    resource = models.URLField(max_length=2048, null=True, blank=True)
    object_type = models.ManyToManyField(ObjectType, blank=True)
    url = models.URLField(max_length=512, null=True, blank=True)
    s3 = models.ForeignKey("projects.S3", null=True, blank=True, on_delete=models.CASCADE)
    bucket = models.CharField(max_length=200, null=True, blank=True, default="models")
    path = models.CharField(max_length=200, null=True, blank=True, default="models")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    tags = TagField(blank=True)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        related_name="model_owner",
        null=True,
    )
    status = models.CharField(max_length=2, choices=STATUS, default=CREATED)
    # tag = models.CharField(max_length=10, default='latest')
    model_card_headline = models.ImageField(upload_to="models/image", null=True, blank=True, default=None)
    docker_image = models.OneToOneField(
        "projects.Environment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        default=None,
    )

    class Meta:
        unique_together = ("name", "version", "project")

    def __str__(self):
        return "{name}:{version}".format(name=self.name, version=self.version)


class ModelLog(models.Model):
    STARTED = "ST"
    DONE = "DO"
    FAILED = "FA"
    STATUS = [
        (STARTED, "Started"),
        (DONE, "Done"),
        (FAILED, "Failed"),
    ]
    run_id = models.CharField(max_length=32)
    trained_model = models.CharField(max_length=32, default="")
    # trained_model = models.ForeignKey(
    #    Model,
    #    on_delete=models.CASCADE
    # )
    project = models.CharField(max_length=255, default="")
    training_started_at = models.CharField(max_length=255)
    # training_started_at = models.DateTimeField(auto_now_add=True)
    execution_time = models.CharField(max_length=255, default="")
    code_version = models.CharField(max_length=255, default="")
    current_git_repo = models.CharField(max_length=255, default="")
    latest_git_commit = models.CharField(max_length=255, default="")
    system_details = models.TextField(blank=True)
    cpu_details = models.TextField(blank=True)
    training_status = models.CharField(max_length=2, choices=STATUS, default=STARTED)

    class Meta:
        unique_together = ("run_id", "trained_model")


class Metadata(models.Model):
    run_id = models.CharField(max_length=32)
    trained_model = models.CharField(max_length=32, default="")
    project = models.CharField(max_length=255, default="")
    model_details = models.TextField(blank=True)
    parameters = models.TextField(blank=True)
    metrics = models.TextField(blank=True)

    class Meta:
        unique_together = ("run_id", "trained_model")


@receiver(pre_save, sender=Model, dispatch_uid="model_pre_save_signal")
def pre_save_model(sender, instance, using, **kwargs):
    # Load version backend
    VERSION_CLASS = import_string(settings.VERSION_BACKEND)
    # Set version
    release_type = instance.release_type
    # If version is not already set, create new release
    if not instance.version:
        # Get latest release and bump:
        model = Model.objects_version.latest(instance.name, instance.project)
        if not model:
            # This is the first release
            new_version = VERSION_CLASS()
        else:
            new_version = VERSION_CLASS(model.version)

        release_status, instance.version = new_version.release(release_type)
        print("New version: " + instance.version)
        if not release_status:
            raise Exception(
                ("Failed to create new release for " "model {}-{}, release type {}.").format(
                    instance.name, instance.version, release_type
                )
            )


@receiver(pre_delete, sender=Model, dispatch_uid="model_pre_delete_signal")
def pre_delete_model(sender, instance, using, **kwargs):
    # Model is saved in bucket 'model' with filename 'instance.uid'
    try:
        client = Minio(
            instance.project.s3storage.host,
            access_key=instance.project.s3storage.access_key,
            secret_key=instance.project.s3storage.secret_key,
            secure=settings.OIDC_VERIFY_SSL,
        )
        client.remove_object("models", instance.uid)
    except Exception:
        print("Failed to delete model object {} from minio store.".format(instance.uid))
