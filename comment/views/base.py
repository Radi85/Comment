from django.views.generic import FormView

from comment.conf import settings
from comment.context import DABContext
from comment.responses import DABResponseData
from comment.messages import EmailInfo
from comment.service.email import DABEmailService
from comment.forms import CommentForm


class BaseCommentView(FormView, DABResponseData):
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = context.pop('form')
        context.update(DABContext(self.request))
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class CommentCreateMixin(BaseCommentView):
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
        self.anonymous = True
        self.msg = EmailInfo.CONFIRMATION_SENT

    def perform_create(self, comment, request, api=False):
        if settings.COMMENT_ALLOW_ANONYMOUS and not comment.user:
            self._handle_anonymous(comment, request, api)
        else:
            comment = self.perform_save(comment, request)
        return comment
