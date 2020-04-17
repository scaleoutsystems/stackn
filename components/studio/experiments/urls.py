from django.urls import path
from . import views

app_name = 'experiments'

urlpatterns = [
    path('<user>/<project>/', views.index, name='index'),
    path('<user>/<project>/run', views.run, name='run'),
    path('<user>/<project>/<str:id>/details', views.details, name='details'),
]

