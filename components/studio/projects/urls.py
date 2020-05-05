from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('projects/', views.index, name='index'),
    path('projects/create', views.create, name='create'),
    path('<user>/<project_slug>', views.details, name='details'),
    path('<user>/<project_slug>/settings', views.settings, name='settings'),
    path('<user>/<project_slug>/delete', views.delete, name='delete'),
    path('<user>/<project_slug>/env/change', views.change_environment, name='change_environment'),
]
