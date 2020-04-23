from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('add', views.add, name='add'),
    path('<int:id>', views.details, name='details'),
    path('<int:id>/visualize', views.visualize_report, name='visualize'),
    path('generator/<int:id>/delete', views.delete_generator, name='delete_generator'),
    path('report/<int:id>/delete', views.delete_report, name='delete_report'),
]
