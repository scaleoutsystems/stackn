from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('apps', views.index, name='index'),
]