from django.urls import path
from . import views

app_name = 'experiments'

urlpatterns = [
    path('', views.index, name='index'),
    path('run', views.run, name='run'),
    path('<str:id>/details', views.details, name='details'),
    path('<str:id>/delete', views.delete, name='delete'),
]

