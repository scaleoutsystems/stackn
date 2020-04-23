from django.urls import path
from . import views

app_name = 'deployments'

urlpatterns = [
    path('deploy/<int:id>', views.deploy, name='deploy'),
    path('undeploy/<int:id>', views.undeploy, name='undeploy'),
    path('', views.index, name='index'),
    path('definition', views.deployment_definition_index, name='deployment_definition_index'),
    path('definition/add', views.deployment_definition_add, name='deployment_definition_add'),
    path('definition/edit/<id>', views.deployment_definition_edit, name='deployment_definition_edit'),

    path('<user>/<project>', views.deployment_index, name='deployment_index'),
    path('<user>/<project>/add', views.deployment_add, name='deployment_add'),
    path('<user>/<project>/edit/<id>', views.deployment_edit, name='deployment_edit'),


]
