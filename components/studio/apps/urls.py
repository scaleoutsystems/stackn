from django.urls import path
from . import views

app_name = 'apps'

urlpatterns = [
    path('', views.index, name='index'),
    path('status', views.get_status, name='get_status'),
    path('<category>', views.filtered, name='filtered'),
    path('<category>/<ai_id>/update', views.update_app, name='update'),
    path('create/<app_slug>', views.create, name='create'),
    path('create/<app_slug>/create_releasename', views.create_releasename, name='create_releasename'),
    path('logs/<ai_id>', views.logs, name='logs'),
    path('settings/<ai_id>', views.appsettings, name='appsettings'),
    path('settings/<ai_id>/add_releasename', views.add_releasename, name='add_releasename'),
    path('settings/<ai_id>/add_tag', views.add_tag, name='add_tag'),
    path('settings/<ai_id>/remove_tag', views.remove_tag, name='remove_tag'),
    path('delete/<category>/<ai_id>', views.delete, name='delete'),
    path('publish/<category>/<ai_id>', views.publish, name='publish'),
]