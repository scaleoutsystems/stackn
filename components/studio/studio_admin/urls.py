from django.urls import path
from . import views

app_name = 'studio_admin'

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:module>', views.load_module_objects, name='load_module_objects')
]
