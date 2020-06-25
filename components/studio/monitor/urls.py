from django.urls import path
from . import views

app_name = 'monitor'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('<resource_type>/cpuchart', views.cpuchart, name='cpuchart')
]