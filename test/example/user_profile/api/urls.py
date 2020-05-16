from django.urls import path, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from user_profile.api import views

urlpatterns = [
    path('users/', views.user_list, name='user-list'),
    re_path(r'^users/(?P<username>[\w]+)$', views.user_detail, name='user-detail'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
