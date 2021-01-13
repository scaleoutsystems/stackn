from django.urls import path
from . import views

app_name = 'studio_admin'

urlpatterns = [
    path('', views.index, name='index'),
    path('activity', views.load_recent_activity, name='recent_activity')
]
