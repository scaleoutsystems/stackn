from django.urls import path
from . import views

app_name = 'models'

urlpatterns = [

    path('', views.index, name='index'),
    path('<user>/<project>/models', views.list, name='list'),
    # path('<user>/<project>/models/create', views.create, name='create'),
    path('<user>/<project>/models/<int:id>', views.details, name='details'),
    path('models/<int:id>', views.details_public, name='details_public'),
    path('<user>/<project>/models/<int:id>/delete', views.delete, name='delete'),
]
