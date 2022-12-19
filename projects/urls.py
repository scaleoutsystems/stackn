from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("projects/", views.index, name="index"),
    path("projects/create", views.create, name="create"),
    path(
        "projects/templates", views.project_templates, name="project_templates"
    ),
    path("<user>/<project_slug>", views.details, name="details"),
    path(
        "<user>/<project_slug>/environments/create",
        views.create_environment,
        name="create_environment",
    ),
    path("<user>/<project_slug>/settings", views.settings, name="settings"),
    path(
        "<user>/<project_slug>/transfer",
        views.transfer_owner,
        name="transfer_owner",
    ),
    path("<user>/<project_slug>/delete", views.delete, name="delete"),
    path(
        "<user>/<project_slug>/setS3storage",
        views.set_s3storage,
        name="set_s3storage",
    ),
    path(
        "<user>/<project_slug>/setmlflow", views.set_mlflow, name="set_mlflow"
    ),
    path(
        "<user>/<project_slug>/createflavor",
        views.create_flavor,
        name="create_flavor",
    ),
    path(
        "<user>/<project_slug>/deleteflavor",
        views.delete_flavor,
        name="delete_flavor",
    ),
    path(
        "<user>/<project_slug>/createenvironment",
        views.create_environment,
        name="create_environment",
    ),
    path(
        "<user>/<project_slug>/deleteenvironment",
        views.delete_environment,
        name="delete_environment",
    ),
    path(
        "<user>/<project_slug>/details/change",
        views.change_description,
        name="change_description",
    ),
    path(
        "<user>/<project_slug>/image/update",
        views.update_image,
        name="update_image",
    ),
    path(
        "<user>/<project_slug>/project/publish",
        views.publish_project,
        name="publish_project",
    ),
    path(
        "<user>/<project_slug>/project/access/grant",
        views.grant_access_to_project,
        name="grant_access",
    ),
    path(
        "<user>/<project_slug>/project/access/revoke",
        views.revoke_access_to_project,
        name="revoke_access",
    ),
]
