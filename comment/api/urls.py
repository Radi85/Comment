from django.urls import path, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from comment.api import views

urlpatterns = [
    path('comments/', views.CommentList.as_view(), name='comments-list'),
    path('comments/create/', views.CommentCreate.as_view(), name='comments-create'),
    re_path(r'^comments/(?P<pk>[0-9]+)$', views.CommentDetail.as_view(), name='comment-detail'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
