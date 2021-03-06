
# from django.contrib import admin
from django.urls import path, include
from . import api_v1

urlpatterns = [
    # path('admin/', admin.site.urls),            # remove this in prod
    path('', include('home.urls', namespace='home')),
    path('user/', include('user.urls', namespace='user')),
    path('api/v1/', include(api_v1, namespace='api_v1')),
    path('proxy/', include('proxy.urls', namespace='proxy')),
]
