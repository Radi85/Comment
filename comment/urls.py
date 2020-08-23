from django.urls import path, re_path

from comment.views import (
    CreateComment, UpdateComment, DeleteComment, SetReaction, SetFlag, ChangeFlagState,
    ConfirmComment)

app_name = 'comment'

urlpatterns = [
    path('create/', CreateComment.as_view(), name='create'),
    path('edit/<int:pk>/', UpdateComment.as_view(), name='edit'),
    path('delete/<int:pk>/', DeleteComment.as_view(), name='delete'),
    path('<int:pk>/react/<str:reaction>/', SetReaction.as_view(), name='react'),
    path('<int:pk>/flag/', SetFlag.as_view(), name='flag'),
    path('<int:pk>/flag/state/change/', ChangeFlagState.as_view(), name='flag-change-state'),
    re_path(r'^confirm/(?P<key>[^/]+)/$', ConfirmComment.as_view(), name='confirm-comment'),
]
