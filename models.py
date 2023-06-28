from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from tagulous.models import TagField


class AppCategories(models.Model):
    name = models.CharField(max_length=512)
    priority = models.IntegerField(default=100)
    slug = models.CharField(max_length=512, default="", primary_key=True)

    def __str__(self):
        return str(self.name)


class Apps(models.Model):
    user_can_create = models.BooleanField(default=True)
    user_can_edit = models.BooleanField(default=True)
    user_can_delete = models.BooleanField(default=True)
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
    def get_app_instances_of_project_filter(
        self, user, project, include_deleted=False, deleted_time_delta=None
    ):
        q = Q()

        if not include_deleted:
            if deleted_time_delta is None:
                q &= ~Q(state="Deleted")
            else:
                time_threshold = datetime.now() - timedelta(
                    minutes=deleted_time_delta
                )
                q &= ~Q(state="Deleted") | Q(deleted_on__gte=time_threshold)

        q &= Q(owner=user) | Q(access__in=["project", "public"])
        q &= Q(project=project)

        return q

    def get_app_instances_of_project(
        self,
        user,
        project,
        filter_func=None,
        order_by=None,
        limit=None,
        override_default_filter=False,
    ):
        if order_by is None:
            order_by = "-created_on"

        if filter_func is None:
            return self.filter(
                self.get_app_instances_of_project_filter(
                    user=user, project=project
                )
            ).order_by(order_by)[:limit]

        if override_default_filter:
            return self.filter(filter_func).order_by(order_by)[:limit]

        return (
            self.filter(
                self.get_app_instances_of_project_filter(
                    user=user, project=project
                )
            )
            .filter(filter_func)
            .order_by(order_by)[:limit]
        )

    def get_available_app_dependencies(self, user, project, app_name):
        result = self.filter(
            ~Q(state="Deleted"),
            Q(owner=user) | Q(access__in=["project", "public"]),
            project=project,
            app__name=app_name,
        )

        if (
            settings.STUDIO_ACCESSMODE == "ReadWriteOnce"
            and app_name == "Persistent Volume"
        ):
            for instance in result:
                exists = self.filter(
                    ~Q(state="Deleted"),
                    project=project,
                    app_dependencies=instance,
                ).exists()

                if exists:
                    result = result.exclude(id=instance.id)

        return result

    def user_can_create(self, user, project, app_slug):
        apps_per_project = (
            {}
            if project.apps_per_project is None
            else project.apps_per_project
        )

        limit = (
            apps_per_project[app_slug]
            if app_slug in apps_per_project
            else None
        )

        app = Apps.objects.get(slug=app_slug)

        if not app.user_can_create:
            return False

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
    tags = TagField(blank=True, null=True)
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
