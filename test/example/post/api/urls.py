from django.urls import path, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from post.api import views

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('posts/', views.PostList.as_view(), name='post-list'),
    re_path(r'^posts/(?P<pk>[0-9]+)$', views.PostDetail.as_view(), name='post-detail'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
