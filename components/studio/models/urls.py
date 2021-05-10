from django.urls import path
from . import views

app_name = 'models'

urlpatterns = [

    path('', views.index, name='index'),
    path('<user>/<project>/models', views.list, name='list'),
    path('<user>/<project>/models/<int:id>', views.details, name='details'),
    path('models/<int:id>', views.details_public, name='details_public'),
    path('<user>/<project>/models/<int:id>/delete', views.delete, name='delete'),
    path('<user>/<project>/models/<int:id>/access', views.change_access, name='change_access'),
    path('<user>/<project>/models/<int:id>/upload', views.upload_image, name='upload_image'),
    path('<user>/<project>/models/<int:id>/docker', views.add_docker_image, name='add_docker_image'),
]
