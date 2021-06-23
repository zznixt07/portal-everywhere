from django.contrib import admin
from django.urls import path, include

app_name = 'api_v1_app'
urlpatterns = [
    path('', lambda: 1, name='index'),
    path('tech/', include('tech_news.urls', namespace='tech_news')),
]