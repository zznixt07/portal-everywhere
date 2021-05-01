from django.urls import path
from . import views

app_name = 'site_campus'
urlpatterns = [
    path('', views.home, name='index'),
]