from django.urls import path
from . import views

app_name = 'ingress'

urlpatterns = [
    path('', views.index, name='index'),
]