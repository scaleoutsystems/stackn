from django.urls import path
from . import views

app_name = 'models'


urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.create, name='create'),
    path('<int:id>', views.details, name='details'),
    path('<int:id>/delete', views.delete, name='delete'),
    path('<int:id>/reports', views.model_reports, name='model_reports'),
]
