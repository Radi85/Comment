from rest_framework import permissions

from comment.conf import settings
from comment.utils import is_comment_admin, is_comment_moderator, can_block_user, can_moderate_flagging
from comment.messages import BlockUserError
from comment.models import BlockedUser


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owner of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # GET, HEAD or OPTIONS requests are SAFE_METHODS.
        if request.method in permissions.SAFE_METHODS:
            return True
        # PUT and DELETE permissions are allowed to the owner of the comment.
        if request.method == 'DELETE':  # comment admin can delete other users comments
            return any([
                is_comment_admin(request.user),
                obj.user == request.user,
                (obj.is_flagged and is_comment_moderator(request.user))
            ])
        return obj.user == request.user


class UserPermittedOrReadOnly(permissions.BasePermission):
    message = BlockUserError.NOT_PERMITTED

    def has_permission(self, request, view):
        data = request.POST or getattr(request, 'data', {})
        return bool(
            request.method in permissions.SAFE_METHODS or
            not BlockedUser.objects.is_user_blocked(request.user.id, data.get('email'))
        )


class CanCreatePermission(permissions.BasePermission):
    """
    This will check if creating comment is permitted
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated or settings.COMMENT_ALLOW_ANONYMOUS


class FlagEnabledPermission(permissions.BasePermission):
    """
    This will check if the COMMENT_FLAGS_ALLOWED is enabled
    """
    def has_permission(self, request, view):
        return bool(getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0))


class CanChangeFlaggedCommentState(permissions.BasePermission):
    def has_permission(self, request, view):
        return can_moderate_flagging(request.user)

    def has_object_permission(self, request, view, obj):
        return obj.is_flagged


class SubscriptionEnabled(permissions.BasePermission):
    """
    This will check if the COMMENT_ALLOW_SUBSCRIPTION is enabled
    """
    def has_permission(self, request, view):
        return getattr(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)


class CanGetSubscribers(SubscriptionEnabled):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return is_comment_admin(request.user) or is_comment_moderator(request.user)


class CanBlockUsers(permissions.BasePermission):
    def has_permission(self, request, view):
        return can_block_user(request.user)
