from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from rest_framework import permissions

from comment.models import Comment
from comment.utils import is_comment_admin, is_comment_moderator


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
            return is_comment_admin(request.user) or obj.user == request.user
        return obj.user == request.user


class ContentTypePermission(permissions.BasePermission):
    """
    This will validate the query params to match a valid ContentType
    """
    message = ""

    def has_permission(self, request, view):
        model_type = request.GET.get("type")
        if not model_type:
            self.message = "model type must be provided"
            return False
        pk = request.GET.get("id")
        if not pk:
            self.message = "model id must be provided"
            return False
        try:
            model_type = model_type.lower()
            ct = ContentType.objects.get(model=model_type).model_class()
            model_class = ct.objects.filter(id=pk)
            if not model_class.exists() and model_class.count() != 1:
                self.message = "this is not a valid id for this model"
                return False
        except ContentType.DoesNotExist:
            self.message = "this is not a valid model type"
            return False
        except ValueError:
            self.message = "type id must be an integer"
            return False

        return True


class ParentIdPermission(permissions.BasePermission):
    """
    This will validate the parent id
    """
    message = ""

    def has_permission(self, request, view):
        model_id = request.GET.get('id')
        parent_id = request.GET.get('parent_id')
        if not parent_id or parent_id == '0':
            return True
        try:
            Comment.objects.get(id=parent_id, object_id=model_id)
        except Comment.DoesNotExist:
            self.message = ("this is not a valid id for a parent comment or "
                            "the parent comment does NOT belong to this model object")
            return False
        except ValueError:
            self.message = "the parent id must be an integer"
            return False
        return True


class FlagEnabledPermission(permissions.BasePermission):
    """
    This will check if the COMMENT_FLAGS_ALLOWED is enabled
    """
    def has_permission(self, request, view):
        return bool(getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0))


class CanChangeFlaggedCommentState(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_comment_admin(request.user) or is_comment_moderator(request.user)

    def has_object_permission(self, request, view, obj):
        return obj.is_flagged and (is_comment_admin(request.user) or is_comment_moderator(request.user))
