from django.urls import path
from . import views

app_name = 'studio_admin'

urlpatterns = [
    path('', views.index, name='index'),
    path('projects', views.load_project_resources, name='project_resources'),
    path('labs', views.load_lab_resources, name='lab_resources'),
    path('deployments', views.load_deployment_resources, name='deployment_resources'),
    path('projects/<project_slug>/remove', views.remove_project, name='remove_project'),
    path('labs/<session_uid>/remove', views.remove_lab_session, name='remove_lab_session'),
    path('deployments/<model_id>/remove', views.remove_deployment, name='remove_deployment')
]
