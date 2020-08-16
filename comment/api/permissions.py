from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions

from comment.conf import settings
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
        model_name = request.GET.get("model_name")
        if not model_name:
            self.message = _("model name must be provided")
            return False
        model_id = request.GET.get("model_id")
        if not model_id:
            self.message = _("model id must be provided")
            return False
        app_name = request.GET.get('app_name')
        if not app_name:
            self.message = _('app name must be provided')
            return False

        try:
            cause = 'app'  # used for identifying the cause in ContentType.DoesNotExist exception
            ContentType.objects.get(app_label=app_name)
            cause = 'model'
            model_name = model_name.lower()
            ct = ContentType.objects.get(model=model_name).model_class()
            model_class = ct.objects.filter(id=model_id)
            if not model_class.exists() and model_class.count() != 1:
                self.message = _("this is not a valid model id for this model")
                return False
        except ContentType.DoesNotExist:
            if cause == 'app':
                self.message = _('this is not a valid app name')
            else:
                self.message = _("this is not a valid model name")
            return False
        except ValueError:
            self.message = _("model id must be an integer")
            return False

        return True


class ParentIdPermission(permissions.BasePermission):
    """
    This will validate the parent id
    """
    message = ""

    def has_permission(self, request, view):
        model_id = request.GET.get('model_id')
        parent_id = request.GET.get('parent_id')
        if not parent_id or parent_id == '0':
            return True
        try:
            Comment.objects.get(id=parent_id, object_id=model_id)
        except Comment.DoesNotExist:
            self.message = _(
                'this is not a valid id for a parent comment or '
                'the parent comment does NOT belong to this model object'
                )
            return False
        except ValueError:
            self.message = _("the parent id must be an integer")
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
