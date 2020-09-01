from django.urls import path
from . import views

app_name = 'monitor'

urlpatterns = [
    path('', views.overview, name='overview'),
    path('<resource_type>/cpuchart', views.cpuchart, name='cpuchart'),
    path('lab/delete/<uid>', views.delete_lab, name='delete_lab'),
    path('serve/delete/<model_id>', views.delete_deployment, name='delete_deployment'),
]