from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from tagulous.models import TagField

from apps.helpers.get_apps_per_project_limit import get_apps_per_project_limit


class AppCategories(models.Model):
    name = models.CharField(max_length=512)
    priority = models.IntegerField(default=100)
    slug = models.CharField(max_length=512, default="", primary_key=True)

    def __str__(self):
        return str(self.name)


class Apps(models.Model):
    user_can_create = models.BooleanField(default=True)
    access = models.CharField(
        max_length=20, blank=True, null=True, default="public"
    )
    category = models.ForeignKey(
        "AppCategories",
        related_name="apps",
        on_delete=models.CASCADE,
        null=True,
    )
    chart = models.CharField(max_length=512)
    chart_archive = models.FileField(upload_to="apps/", null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True, default="")
    logo = models.CharField(max_length=512, null=True, blank=True)
    name = models.CharField(max_length=512)
    priority = models.IntegerField(default=100)
    projects = models.ManyToManyField("projects.Project")
    revision = models.IntegerField(default=1)
    settings = models.JSONField(blank=True, null=True)
    slug = models.CharField(max_length=512, blank=True, null=True)
    table_field = models.JSONField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "slug",
            "revision",
        )

    def __str__(self):
        return str(self.name) + "({})".format(self.revision)


class AppInstanceManager(models.Manager):
    def user_can_create(self, user, project, app_slug):
        limit = get_apps_per_project_limit(app_slug)

        num_of_app_instances = self.filter(
            ~Q(state="Deleted"),
            app__slug=app_slug,
            project=project,
        ).count()

        has_perm = user.has_perm("apps.add_appinstance")

        return limit is None or limit > num_of_app_instances or has_perm


class AppInstance(models.Model):
    objects = AppInstanceManager()

    access = models.CharField(
        max_length=20, default="private", null=True, blank=True
    )
    app = models.ForeignKey(
        "Apps", on_delete=models.CASCADE, related_name="appinstance"
    )
    app_dependencies = models.ManyToManyField("apps.AppInstance", blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    info = models.JSONField(blank=True, null=True)
    model_dependencies = models.ManyToManyField("models.Model", blank=True)
    name = models.CharField(max_length=512, default="app_name")
    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="app_owner",
        null=True,
    )
    parameters = models.JSONField(blank=True, null=True)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="appinstance",
    )
    state = models.CharField(max_length=50, null=True, blank=True)
    table_field = models.JSONField(blank=True, null=True)
    tags = TagField()
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [("can_access_app", "Can access app service")]

    def __str__(self):
        return str(self.name) + " ({})-{}-{}-{}".format(
            self.state, self.owner, self.app.name, self.project
        )


@receiver(
    post_save,
    sender=AppInstance,
    dispatch_uid="app_instance_update_permission",
)
def update_permission(sender, instance, created, **kwargs):
    owner = instance.owner

    if instance.access == "private":
        if created or not owner.has_perm("can_access_app", instance):
            assign_perm("can_access_app", owner, instance)

    else:
        if owner.has_perm("can_access_app", instance):
            remove_perm("can_access_app", owner, instance)


class AppStatus(models.Model):
    appinstance = models.ForeignKey(
        "AppInstance", on_delete=models.CASCADE, related_name="status"
    )
    info = models.JSONField(blank=True, null=True)
    status_type = models.CharField(max_length=15, default="app_name")
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "time"

    def __str__(self):
        return str(self.appinstance.name) + "({})".format(self.time)


class ResourceData(models.Model):
    appinstance = models.ForeignKey(
        "AppInstance", on_delete=models.CASCADE, related_name="resourcedata"
    )
    cpu = models.IntegerField()
    gpu = models.IntegerField()
    mem = models.IntegerField()
    time = models.IntegerField()
