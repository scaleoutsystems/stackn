from django.urls import path
from . import views

app_name = 'apps'

urlpatterns = [
    path('', views.index, name='index'),
    path('<app_slug>', views.create, name='create'),
    path('delete/<ai_id>', views.delete, name='delete'),
]