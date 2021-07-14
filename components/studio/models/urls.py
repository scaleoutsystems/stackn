from django.urls import path
from . import views

app_name = 'models'

urlpatterns = [

    path('', views.index, name='index'),
    path('<user>/<project>/models', views.list, name='list'),
    path('<user>/<project>/models/<int:id>', views.details_private, name='details_private'),
    path('models/<int:id>', views.details_public, name='details_public'),
    path('models/<int:published_id>/<int:id>/add_tag', views.add_tag, name='add_tag'),
    path('models/<int:published_id>/<int:id>/remove_tag', views.remove_tag, name='remove_tag'),
    path('<user>/<project>/models/<int:id>/delete', views.delete, name='delete'),
    path('<user>/<project>/models/<int:id>/publish', views.publish_model, name='publish_model'),
    path('<user>/<project>/models/<int:id>/unpublish', views.unpublish_model, name='unpublish_model'),
    path('<user>/<project>/models/<int:id>/access', views.change_access, name='change_access'),
    path('<user>/<project>/models/<int:id>/upload', views.upload_model_headline, name='upload_model_headline'),
    path('<user>/<project>/models/<int:id>/docker', views.add_docker_image, name='add_docker_image'),
]
