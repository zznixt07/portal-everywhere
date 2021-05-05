from django.urls import path, include
from . import views

feeds = [
    path('', lambda: 1, name='index'),
    path('xda/', views.xda, name='xda'),
    path('torrentfreak/', views.torrentfreak, name='torrentfreak'),
]

app_name = 'tech_news_app'
urlpatterns = [
    path('feeds/', include((feeds, 'feeds'), namespace='feeds')),
]