from django.urls import path
from . import views

app_name = 'studio_admin'

urlpatterns = [
    path('', views.index, name='index'),
    path('delete_project/<project_slug>', views.delete_project, name='delete_project'),
]
