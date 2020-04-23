from django.urls import path
from . import views

app_name = 'workflows'


urlpatterns = [
    path('definition', views.workflows_definition_index, name='workflows_definition_index'),
    path('definition/add', views.workflows_definition_add, name='workflows_definition_add'),
    path('definition/edit/<id>', views.workflows_definition_edit, name='workflows_definition_edit'),
    path('<user>/<project>/', views.workflows_index, name='workflows_index'),
    path('<user>/<project>/run', views.workflows_run, name='workflows_run'),
    path('<user>/<project>/<id>', views.workflows_details, name='workflows_details'),

]

