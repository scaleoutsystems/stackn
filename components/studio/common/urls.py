from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'common'

urlpatterns = [
    path('', views.HomeView.as_view(), name='landing'),
    path('welcome/', views.HomeView.as_view(), name='welcome'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
]
