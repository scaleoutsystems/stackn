from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('projects/', views.index, name='index'),
    path('projects/create', views.create, name='create'),
    path('<user>/<project_slug>', views.details, name='details'),
    path('<user>/<project_slug>/settings', views.settings, name='settings'),
    path('<user>/<project_slug>/delete', views.delete, name='delete'),
    path('<user>/<project_slug>/details/change', views.change_description, name='change_description'),
    path('<user>/<project_slug>/project/publish', views.publish_project, name='publish_project'),
    path('<user>/<project_slug>/project/access/grant', views.grant_access_to_project, name='grant_access'),
    path('<user>/<project_slug>/project/access/revoke', views.revoke_access_to_project, name='revoke_access'),
    path('<user>/<project_slug>/logs', views.load_project_activity, name='project_activity'),
]
