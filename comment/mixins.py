import abc

from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.utils.translation import gettext_lazy as _

from comment.conf import settings
from comment.utils import is_comment_admin, is_comment_moderator
from comment.validators import ValidatorMixin


class AJAXRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.META.get('HTTP_X_REQUESTED_WITH', None) == 'XMLHttpRequest':
            return HttpResponseBadRequest(_('Only AJAX request are allowed'))
        return super().dispatch(request, *args, **kwargs)


class BasePermission(AJAXRequiredMixin):
    def has_permission(self, request):
        return True

    def has_object_permission(self, request, obj):
        return True


class BaseCommentMixin(LoginRequiredMixin, BasePermission):
    pass


class CanCreateMixin(BasePermission, AccessMixin, ValidatorMixin):
    def has_permission(self, request):
        return request.user.is_authenticated or settings.COMMENT_ALLOW_ANONYMOUS

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ObjectLevelMixin(BaseCommentMixin):
    @abc.abstractmethod
    def get_object(self):
        raise ImproperlyConfigured(
            _("Your %s class has not defined a get_object() method, which is required.")
            % self.__class__.__name__
        )


class CanEditMixin(ObjectLevelMixin, ValidatorMixin, abc.ABC):
    def has_object_permission(self, request, obj):
        return request.user == obj.user

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_object_permission(request, obj):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CanDeleteMixin(ObjectLevelMixin, ValidatorMixin, abc.ABC):
    def has_object_permission(self, request, obj):
        return request.user == obj.user or is_comment_admin(request.user) \
                or (obj.is_flagged and is_comment_moderator(request.user))

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_object_permission(request, obj):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class BaseFlagMixin(ObjectLevelMixin, abc.ABC):
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0):
            return HttpResponseForbidden(_('Flagging system must be enabled'))
        return super().dispatch(request, *args, **kwargs)


class CanSetFlagMixin(BaseFlagMixin, abc.ABC):
    def has_object_permission(self, request, obj):
        """user cannot flag their own comment"""
        return obj.user != request.user

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not self.has_object_permission(request, obj):
            self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CanEditFlagStateMixin(BaseFlagMixin, abc.ABC):
    def has_permission(self, request):
        return is_comment_admin(request.user) or is_comment_moderator(request.user)

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.is_flagged:
            return HttpResponseBadRequest(_('Object must be flagged!'))
        if not self.has_permission(request):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
