from django.urls import path, re_path, include
from . import views

app_name = 'proxy_app'
urlpatterns = [
    path('', views.index, name='index'),
    path('<path:url>', views.proxier, name='proxy-path'),
    # re_path(r'(?P<url>.*)', views.proxier, name='proxy-path'),
]