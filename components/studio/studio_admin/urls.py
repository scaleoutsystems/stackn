from django.urls import path
from . import views

app_name = 'studio_admin'

urlpatterns = [
    path('', views.index, name='index'),
    path('projects', views.load_project_resources, name='project_resources'),
    path('labs', views.load_lab_resources, name='lab_resources'),
    path('deployments', views.load_deployment_resources, name='deployment_resources')
]
