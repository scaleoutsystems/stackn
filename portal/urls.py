from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("portal/home", views.HomeView.as_view(), name="home"),
    path("about", views.about, name="about"),
    path("teaching", views.teaching, name="teaching"),
    path("privacy", views.privacy, name="privacy"),
    path("apps", views.public_apps, name="apps"),
    path("", views.HomeView.as_view(), name="about-page"),
]
