from django.urls import path
from . import views

app_name = 'apps'

urlpatterns = [
    path('', views.index, name='index'),
    path('<category>', views.filtered, name='filtered'),
    path('create/<app_slug>', views.create, name='create'),
    path('delete/<ai_id>', views.delete, name='delete'),
]