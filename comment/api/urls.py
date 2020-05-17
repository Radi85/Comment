from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from comment.api import views
from comment.views import SetReaction

urlpatterns = [
    path('comments/', views.CommentList.as_view(), name='comments-list'),
    path('comments/create/', views.CommentCreate.as_view(), name='comments-create'),
    path('comments/<int:pk>/', views.CommentDetail.as_view(), name='comment-detail'),
    path('comments/<int:comment_id>/react/<str:reaction>/', SetReaction.as_view(), name='comments-react')
]

urlpatterns = format_suffix_patterns(urlpatterns)
