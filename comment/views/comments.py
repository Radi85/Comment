from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import FormView
from django.utils import timezone
from django.views import View
from django.contrib import messages

from comment.models import Comment
from comment.forms import CommentForm
from comment.utils import (
    get_comment_context_data, get_comment_from_key, get_user_for_request, CommentFailReason
)
from comment.mixins import CanCreateMixin, CanEditMixin, CanDeleteMixin
from comment.conf import settings
from comment.messages import EmailError, EmailInfo
from comment.service.email import DABEmailService


class BaseCommentView(FormView):
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = context.pop('form')
        context.update(get_comment_context_data(self.request))
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class CreateComment(CanCreateMixin, BaseCommentView):
    comment = None
    email_service = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.comment
        return context

    def get_template_names(self):
        if self.request.user.is_anonymous or self.comment.is_parent:
            return ['comment/comments/base.html']
        else:
            return ['comment/comments/child_comment.html']

    def form_valid(self, form):
        user = get_user_for_request(self.request)

        comment_content = form.cleaned_data['content']
        email = form.cleaned_data.get('email', None) or user.email
        time_posted = timezone.now()
        _comment = Comment(
            content_object=self.model_obj,
            content=comment_content,
            user=user,
            parent=self.parent_comment,
            email=email,
            posted=time_posted
        )

        self.email_service = DABEmailService(_comment, self.request)

        if settings.COMMENT_ALLOW_ANONYMOUS and not user:
            # send response, please verify your email to post this comment.
            self.email_service.send_confirmation_request()
            messages.info(self.request, EmailInfo.CONFIRMATION_SENT)
        else:
            _comment.save()
            if settings.COMMENT_ALLOW_SUBSCRIPTION:
                self.email_service.send_notification_to_followers()
            self.comment = _comment

        return self.render_to_response(self.get_context_data())


class UpdateComment(CanEditMixin, BaseCommentView):
    comment = None

    def get_object(self):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        return self.comment

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['comment_form'] = CommentForm(instance=self.comment, request=self.request)
        context['comment'] = self.comment
        return render(request, 'comment/comments/update_comment.html', context)

    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST, instance=self.comment, request=self.request)
        context = self.get_context_data()
        if form.is_valid():
            form.save()
            context['comment'] = self.comment
            return render(request, 'comment/comments/comment_content.html', context)


class DeleteComment(CanDeleteMixin, BaseCommentView):
    comment = None

    def get_object(self):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        return self.comment

    def get(self, request, *args, **kwargs):
        data = dict()
        context = self.get_context_data()
        context["comment"] = self.comment
        context['has_parent'] = not self.comment.is_parent
        data['html_form'] = render_to_string('comment/comments/comment_modal.html', context, request=request)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        self.comment.delete()
        context = self.get_context_data()
        return render(request, 'comment/comments/base.html', context)


class ConfirmComment(View):
    email_service = None

    def get(self, request, *args, **kwargs):
        key = kwargs.get('key', None)
        temp_comment = get_comment_from_key(key)
        if temp_comment.why_invalid == CommentFailReason.BAD:
            messages.error(request, EmailError.BROKEN_VERIFICATION_LINK)
        elif temp_comment.why_invalid == CommentFailReason.EXISTS:
            messages.warning(request, EmailError.USED_VERIFICATION_LINK)
        if not temp_comment.is_valid:
            return render(request, template_name='comment/anonymous/discarded.html')

        comment = temp_comment.obj
        comment.save()
        comment.refresh_from_db()
        if settings.COMMENT_ALLOW_SUBSCRIPTION:
            self.email_service = DABEmailService(comment, request)
            self.email_service.send_notification_to_followers()
        return redirect(comment.get_url(request))
