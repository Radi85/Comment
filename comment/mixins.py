import abc

from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest, HttpResponseForbidden

from comment.conf import settings
from comment.utils import is_comment_admin, is_comment_moderator
from comment.validators import ValidatorMixin
from comment.messages import ErrorMessage, FlagError, FollowError
from comment.service.email import DABEmailService
from comment.messages import EmailInfo


class AJAXRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.META.get('HTTP_X_REQUESTED_WITH', None) == 'XMLHttpRequest':
            return HttpResponseBadRequest(ErrorMessage.NON_AJAX_REQUEST)
        return super().dispatch(request, *args, **kwargs)


class BasePermission(AJAXRequiredMixin):
    def has_permission(self, request):
        return True

    def has_object_permission(self, request, obj):
        return True


class BaseCommentMixin(LoginRequiredMixin, BasePermission):
    pass


class CommentCreateMixin:
    email_service = None

    def _initialize_email_service(self, comment, request):
        self.email_service = DABEmailService(comment, request)

    def _send_notification_to_followers(self, comment, request):
        if settings.COMMENT_ALLOW_SUBSCRIPTION:
            self._initialize_email_service(comment, request)
            self.email_service.send_notification_to_followers()

    def perform_save(self, comment, request):
        comment.save()
        self._send_notification_to_followers(comment, request)
        comment.refresh_from_db()
        return comment

    def _handle_anonymous(self, comment, request, api=False):
        self._initialize_email_service(comment, request)
        self.email_service.send_confirmation_request(api=api)
        if not api:
            messages.info(request, EmailInfo.CONFIRMATION_SENT)

    def perform_create(self, comment, request, api=False):

        if settings.COMMENT_ALLOW_ANONYMOUS and not comment.user:
            self._handle_anonymous(comment, request, api)
        else:
            comment = self.perform_save(comment, request)
        return comment


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
            ErrorMessage.METHOD_NOT_IMPLEMENTED.format(class_name=self.__class__.__name__, method_name='get_object()')
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
        if not getattr(settings, 'COMMENT_FLAGS_ALLOWED', False):
            return HttpResponseForbidden(FlagError.SYSTEM_NOT_ENABLED)
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
            return HttpResponseBadRequest(FlagError.NOT_FLAGGED_OBJECT)
        if not self.has_permission(request):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class CanSubscribeMixin(BaseCommentMixin):
    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False):
            return HttpResponseForbidden(FollowError.SYSTEM_NOT_ENABLED)
        return super().dispatch(request, *args, **kwargs)
