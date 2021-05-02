from django.urls import path, re_path
from django.views.decorators.cache import cache_page
from django.views.i18n import JavaScriptCatalog

from comment import __version__
from comment.views import (
    CreateComment, UpdateComment, DeleteComment, SetReaction, SetFlag, ChangeFlagState,
    ConfirmComment, ToggleFollowView, ToggleBlockingView
)

app_name = 'comment'


urlpatterns = [
    path('create/', CreateComment.as_view(), name='create'),
    path('edit/<int:pk>/', UpdateComment.as_view(), name='edit'),
    path('delete/<int:pk>/', DeleteComment.as_view(), name='delete'),
    path('<int:pk>/react/<str:reaction>/', SetReaction.as_view(), name='react'),
    path('<int:pk>/flag/', SetFlag.as_view(), name='flag'),
    path('<int:pk>/flag/state/change/', ChangeFlagState.as_view(), name='flag-change-state'),
    re_path(r'^confirm/(?P<key>[^/]+)/$', ConfirmComment.as_view(), name='confirm-comment'),
    path('toggle-subscription/', ToggleFollowView.as_view(), name='toggle-subscription'),
    path('toggle-blocking/', ToggleBlockingView.as_view(), name='toggle-blocking'),
    # javascript translations
    # The value returned by _get_version() must change when translations change.
    path(
        'jsi18n/',
        cache_page(86400, key_prefix='js18n-%s' % __version__)(JavaScriptCatalog.as_view()),
        name='javascript-catalog'),
]
