from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views
from .views import (
    GrantAccessToProjectView,
    RevokeAccessToProjectView,
    UpdatePatternView,
)

app_name = "projects"

basicpatterns = [
    path("projects/", views.IndexView.as_view(), name="index"),
    path(
        "projects/create",
        login_required(views.CreateProjectView.as_view()),
        name="create",
    ),
    path(
        "projects/templates", views.project_templates, name="project_templates"
    ),
    path("<user>/<project_slug>", views.DetailsView.as_view(), name="details"),
    path(
        "<user>/<project_slug>/environments/create",
        views.create_environment,
        name="create_environment",
    ),
    path("<user>/<project_slug>/settings", views.settings, name="settings"),
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
        "<user>/<project_slug>/details/change",
        views.change_description,
        name="change_description",
    ),
    path(
        "<user>/<project_slug>/pattern/update",
        UpdatePatternView.as_view(),
        name="update_pattern",
    ),
    path(
        "<user>/<project_slug>/project/publish",
        views.publish_project,
        name="publish_project",
    ),
    path(
        "<user>/<project_slug>/project/access/grant",
        GrantAccessToProjectView.as_view(),
        name="grant_access",
    ),
    path(
        "<user>/<project_slug>/project/access/revoke",
        RevokeAccessToProjectView.as_view(),
        name="revoke_access",
    ),
]

extrapatterns = [
    path(
        "<user>/<project_slug>/environments/create",
        views.create_environment,
        name="create_environment",
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
]

if settings.ENABLE_PROJECT_EXTRA_SETTINGS:
    urlpatterns = basicpatterns + extrapatterns
else:
    urlpatterns = basicpatterns
