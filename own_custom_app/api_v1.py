from django.contrib import admin
from django.urls import path, include

app_name = 'api_v1_app'
urlpatterns = [
    path('', lambda: 1, name='index'),
    path('campus/', include('campus.urls', namespace='campus')),
    path('tech/', include('tech_news.urls', namespace='tech_news')),
]