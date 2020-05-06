from django.urls import path
from . import views

app_name = 'deployments'

urlpatterns = [
    path('deployments/', views.index, name='index'),
    path('deployments/deploy/<int:id>', views.deploy, name='deploy'),
    path('deployments/undeploy/<int:id>', views.undeploy, name='undeploy'),
    path('deployments/definition', views.deployment_definition_index, name='deployment_definition_index'),
    path('deployments/definition/add', views.deployment_definition_add, name='deployment_definition_add'),
    path('deployments/definition/edit/<id>', views.deployment_definition_edit, name='deployment_definition_edit'),
    path('<user>/<project>/deployments/', views.deployment_index, name='deployment_index'),
    path('<user>/<project>/deployments/edit/<id>', views.deployment_edit, name='deployment_edit'),
]
