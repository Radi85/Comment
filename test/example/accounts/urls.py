from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import login, logout
from . import views

app_name = 'accounts'

urlpatterns = [
    re_path(r'^profile/(?P<username>[.@_+\w-]+)$', views.user_profile, name='profile'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', login, {'template_name':'accounts/login.html'}, name='login'),
    path('logout/', logout, name='logout'),
]
