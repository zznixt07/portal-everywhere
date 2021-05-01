from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('campus/', include('campus.urls', namespace='campus')),
    path('tech/', include('tech_news.urls', namespace='tech_news')),
]