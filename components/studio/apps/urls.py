from django.urls import path
from . import views

app_name = 'apps'

urlpatterns = [
    path('', views.index, name='index'),
    path('status', views.get_status, name='get_status'),
    path('<category>', views.filtered, name='filtered'),
    path('create/<app_slug>', views.create, name='create'),
    path('logs/<ai_id>', views.logs, name='logs'),
    path('settings/<ai_id>', views.appsettings, name='appsettings'),
    path('delete/<category>/<ai_id>', views.delete, name='delete'),
]