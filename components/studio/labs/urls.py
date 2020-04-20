from django.urls import path
from . import views

app_name = 'labs'

urlpatterns = [
    path('', views.index, name='index'),
    path('run/', views.run, name='run'),
    path('delete/<id>', views.delete, name='delete'),
]
