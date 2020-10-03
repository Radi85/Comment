from django.urls import path, re_path
from rest_framework.urlpatterns import format_suffix_patterns

from comment.api import views

urlpatterns = [
    path('comments/', views.CommentList.as_view(), name='comments-list'),
    path('comments/create/', views.CommentCreate.as_view(), name='comments-create'),
    path('comments/<int:pk>/', views.CommentDetail.as_view(), name='comment-detail'),
    path('comments/<int:pk>/react/<str:reaction>/', views.CommentDetailForReaction.as_view(), name='comments-react'),
    path('comments/<int:pk>/flag/', views.CommentDetailForFlag.as_view(), name='comments-flag'),
    path(
        'comments/<int:pk>/flag/state/change/',
        views.CommentDetailForFlagStateChange.as_view(),
        name='comments-flag-state-change'
    ),
    re_path(r'^comments/confirm/(?P<key>[^/]+)/$', views.ConfirmComment.as_view(), name='confirm-comment'),
    path('comments/toggle-subscription/', views.ToggleFollowAPI.as_view(), name='toggle-subscription'),
    path('comments/subscribers/', views.SubscribersAPI.as_view(), name='subscribers'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
