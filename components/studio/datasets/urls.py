from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    path('<int:page_index>', views.page, name='page'),
    path('<int:page_index>/datasheet', views.datasheet, name='datasheet'),
]
