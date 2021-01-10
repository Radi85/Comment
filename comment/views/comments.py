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
from comment.mixins import CanCreateMixin, CanEditMixin, CanDeleteMixin, CommentCreateMixin
from comment.messages import EmailError


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


class CreateComment(CanCreateMixin, BaseCommentView, CommentCreateMixin):
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
        temp_comment = Comment(
            content_object=self.model_obj,
            content=comment_content,
            user=user,
            parent=self.parent_comment,
            email=email,
            posted=time_posted
        )
        self.comment = self.perform_create(temp_comment, self.request)

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


class ConfirmComment(View, CommentCreateMixin):
    email_service = None

    @staticmethod
    def _handle_invalid_comment(comment, request):
        if comment.why_invalid == CommentFailReason.BAD:
            messages.error(request, EmailError.BROKEN_VERIFICATION_LINK)
        elif comment.why_invalid == CommentFailReason.EXISTS:
            messages.warning(request, EmailError.USED_VERIFICATION_LINK)

    def get(self, request, *args, **kwargs):
        key = kwargs.get('key', None)
        temp_comment = get_comment_from_key(key)
        self._handle_invalid_comment(temp_comment, request)

        if not temp_comment.is_valid:
            return render(request, template_name='comment/anonymous/discarded.html')

        comment = self.perform_save(temp_comment.obj, request)

        return redirect(comment.get_url(request))
