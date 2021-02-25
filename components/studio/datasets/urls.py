from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    path('', views.page, name='page'),
]
