from django.urls import path

from . import views

app_name = "apps"

urlpatterns = [
    path("apps/", views.index, name="index"),
    path("status", views.get_status, name="get_status"),
    path("<category>", views.filtered, name="filtered"),
    path("create/<app_slug>", views.create, name="create"),
    path("logs/<ai_id>", views.logs, name="logs"),
    path("settings/<ai_id>", views.appsettings, name="appsettings"),
    path("settings/<ai_id>/add_tag", views.add_tag, name="add_tag"),
    path("settings/<ai_id>/remove_tag", views.remove_tag, name="remove_tag"),
    path("delete/<category>/<ai_id>", views.delete, name="delete"),
    path("publish/<category>/<ai_id>", views.publish, name="publish"),
    path("unpublish/<category>/<ai_id>", views.unpublish, name="unpublish"),
]
