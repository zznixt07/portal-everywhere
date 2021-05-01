
from django.urls import path, include
from . import views

app_name = 'site_user'
urlpatterns = [
    path('signup/', views.OwnSignupView.as_view(), name='signup'),
    path('login/', views.OwnLoginView.as_view(), name='login'),
    path('logout/', views.OwnLogoutView.as_view(), name='logout'),
    
    # path('login/', views.login, name='login'),
    # path('signup/', views.signup, name='signup'),
    path('viewUsers/', views.view_users, name='view'),
]
