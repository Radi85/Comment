from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.views.generic import FormView
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views import View
from django.contrib import messages

from comment.models import Comment
from comment.forms import CommentForm
from comment.utils import (
    get_comment_context_data, get_model_obj, is_comment_admin, is_comment_moderator,
    get_comment_from_key, process_anonymous_commenting, get_user_for_request, CommentFailReason)
from comment.mixins import BaseCommentMixin, AJAXRequiredMixin
from comment.conf import settings


class BaseCommentView(AJAXRequiredMixin, FormView):
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = context.pop('form')
        context.update(get_comment_context_data(self.request))
        return context

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['request'] = self.request
        return kw


class CreateComment(BaseCommentView):
    comment = None

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
        app_name = self.request.POST.get('app_name')
        model_name = self.request.POST.get('model_name')
        model_id = self.request.POST.get('model_id')
        model_object = get_model_obj(app_name, model_name, model_id)
        parent_id = self.request.POST.get('parent_id')
        parent_comment = Comment.objects.get_parent_comment(parent_id)
        user = get_user_for_request(self.request)

        comment_content = form.cleaned_data['content']
        email = form.cleaned_data.get('email', None) or user.email
        time_posted = timezone.now()
        comment = Comment(
            content_object=model_object,
            content=comment_content,
            user=user,
            parent=parent_comment,
            email=email,
            posted=time_posted
            )

        if settings.COMMENT_ALLOW_ANONYMOUS and not user:
            # send response, please verify your email to post this comment.
            response_msg = process_anonymous_commenting(self.request, comment)
            messages.info(self.request, response_msg)
        else:
            comment.save()
            self.comment = comment

        return self.render_to_response(self.get_context_data())


class UpdateComment(BaseCommentMixin, BaseCommentView):
    comment = None

    def dispatch(self, request, *args, **kwargs):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if request.user != self.comment.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

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


class DeleteComment(BaseCommentMixin, BaseCommentView):
    comment = None

    def dispatch(self, request, *args, **kwargs):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if request.user != self.comment.user and not is_comment_admin(request.user) \
                and not (self.comment.is_flagged and is_comment_moderator(request.user)):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

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
    def get(self, request, *args, **kwargs):
        key = kwargs.get('key', None)
        comment = get_comment_from_key(key)

        if comment.why_invalid == CommentFailReason.BAD:
            messages.error(request, _('The link seems to be broken.'))
        elif comment.why_invalid == CommentFailReason.EXISTS:
            messages.warning(request, _('The comment has already been verified.'))

        if not comment.is_valid:
            return render(request, template_name='comment/anonymous/discarded.html')

        return redirect(comment.obj.get_url(request))
