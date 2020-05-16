from django.urls import path, re_path
from django.contrib.auth.views import LoginView, LogoutView

from . import views

app_name = 'profile'

urlpatterns = [
    re_path(r'^profile/(?P<username>[.@_+\w-]+)$', views.user_profile, name='profile'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
