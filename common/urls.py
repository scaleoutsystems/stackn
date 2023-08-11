from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

app_name = "common"

urlpatterns = [
    path("success/", views.RegistrationCompleteView.as_view(), name="success"),
    path("signup/", views.SignUpView.as_view(), name="signup"),
]
