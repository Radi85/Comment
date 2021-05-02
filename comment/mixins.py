import abc

from django.core.exceptions import ImproperlyConfigured

from comment.conf import settings
from comment.utils import is_comment_admin, is_comment_moderator, can_block_user, can_moderate_flagging
from comment.validators import ValidatorMixin
from comment.messages import ErrorMessage, FlagError, FollowError, BlockUserError
from comment.responses import UTF8JsonResponse
from comment.models import BlockedUser


class AJAXRequiredMixin:
    status = 403
    reason = ErrorMessage.NON_AJAX_REQUEST

    def dispatch(self, request, *args, **kwargs):
        if not request.META.get('HTTP_X_REQUESTED_WITH', None) == 'XMLHttpRequest':
            data = {'status': self.status, 'reason': self.reason}
            return UTF8JsonResponse(status=self.status, data=data)
        return super().dispatch(request, *args, **kwargs)


class BasePermission(AJAXRequiredMixin):
    reason = ErrorMessage.NOT_AUTHORIZED

    def has_permission(self, request):
        return True

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request):
            data = {'status': self.status, 'reason': self.reason}
            return UTF8JsonResponse(status=self.status, data=data)
        return super().dispatch(request, *args, **kwargs)


class UserPermission(BasePermission):
    reason = BlockUserError.NOT_PERMITTED

    def has_permission(self, request):
        return not BlockedUser.objects.is_user_blocked(request.user.id, request.POST.get('email'))


class BaseCommentPermission(UserPermission):
    def has_permission(self, request):
        if not request.user.is_authenticated:
            self.reason = ErrorMessage.LOGIN_REQUIRED
            return False
        return super().has_permission(request)


class BaseCommentMixin(BaseCommentPermission):
    pass


class BaseCreatePermission(UserPermission):
    def has_permission(self, request):
        if not settings.COMMENT_ALLOW_ANONYMOUS and not request.user.is_authenticated:
            self.reason = ErrorMessage.LOGIN_REQUIRED
            return False
        return super().has_permission(request)


class CanCreateMixin(BaseCreatePermission, ValidatorMixin):
    pass


class ObjectLevelMixin(BaseCommentPermission):
    @abc.abstractmethod
    def get_object(self):
        raise ImproperlyConfigured(
            ErrorMessage.METHOD_NOT_IMPLEMENTED.format(class_name=self.__class__.__name__, method_name='get_object()')
        )

    def has_object_permission(self, request, obj):
        return True

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_object_permission(request, obj):
            self.reason = ErrorMessage.NOT_AUTHORIZED
            data = {'status': self.status, 'reason': self.reason}
            return UTF8JsonResponse(status=self.status, data=data)
        return super().dispatch(request, *args, **kwargs)


class CanEditMixin(ObjectLevelMixin, ValidatorMixin, abc.ABC):
    def has_object_permission(self, request, obj):
        return request.user == obj.user


class CanDeleteMixin(ObjectLevelMixin, ValidatorMixin, abc.ABC):
    def has_object_permission(self, request, obj):
        return bool(
            request.user == obj.user or
            is_comment_admin(request.user) or
            (obj.is_flagged and is_comment_moderator(request.user))
        )


class BaseFlagPermission(BasePermission):
    def has_permission(self, request):
        if not settings.COMMENT_FLAGS_ALLOWED:
            self.reason = FlagError.SYSTEM_NOT_ENABLED
            return False
        return super().has_permission(request)


class CanSetFlagMixin(BaseFlagPermission, ObjectLevelMixin, abc.ABC):
    def has_object_permission(self, request, obj):
        """user cannot flag their own comment"""
        return obj.user != request.user


class CanUpdateFlagStateMixin(BaseFlagPermission, ObjectLevelMixin, abc.ABC):
    def has_permission(self, request):
        if not can_moderate_flagging(request.user):
            self.reason = ErrorMessage.NOT_AUTHORIZED
            return False
        return super().has_permission(request)

    def has_object_permission(self, request, obj):
        if not obj.is_flagged:
            self.reason = FlagError.NOT_FLAGGED_OBJECT
        return obj.is_flagged


class CanSubscribeMixin(BaseCommentMixin):
    def has_permission(self, request):
        if not settings.COMMENT_ALLOW_SUBSCRIPTION:
            self.reason = FollowError.SYSTEM_NOT_ENABLED
            return False
        return super().has_permission(request)


class CanBlockUsersMixin(BaseCommentMixin):
    reason = ErrorMessage.NOT_AUTHORIZED

    def has_permission(self, request):
        return can_block_user(request.user)
