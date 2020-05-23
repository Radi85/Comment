from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.views.generic import FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from comment.models import Comment
from comment.forms import CommentForm
from comment.utils import get_comment_context_data, get_model_obj


class BaseCommentView(FormView, LoginRequiredMixin):
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = context.pop('form')
        context.update(get_comment_context_data(self.request))
        return context

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest('Only AJAX request are allowed')
        return super().post(request, *args, **kwargs)


class CreateComment(BaseCommentView):
    created_comment = None
    parent_comment = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.created_comment
        return context

    def get_template_names(self):
        if self.created_comment.is_parent:
            return ['comment/base.html']
        else:
            return ['comment/child_comment.html']

    def form_valid(self, form):
        model_object = get_model_obj(self.request)
        parent_id = self.request.POST.get('parent_id')
        if parent_id:
            parent_qs = Comment.objects.filter(id=parent_id)
            if parent_qs.exists():
                self.parent_comment = parent_qs.first()
        comment_content = form.cleaned_data['content']
        self.created_comment = Comment.objects.create(
            content_object=model_object,
            content=comment_content,
            user=self.request.user,
            parent=self.parent_comment,
        )
        return self.render_to_response(self.get_context_data())


class UpdateComment(BaseCommentView):
    updated_comment = None

    def get(self, request, *args, **kwargs):
        self.updated_comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if request.user != self.updated_comment.user:
            raise PermissionDenied
        context = self.get_context_data()
        context['comment_form'] = CommentForm(instance=self.updated_comment)
        context['comment'] = self.updated_comment
        return render(request, 'comment/update_comment.html', context)

    def post(self, request, *args, **kwargs):
        self.updated_comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if request.user != self.updated_comment.user:
            raise PermissionDenied
        form = CommentForm(request.POST, instance=self.updated_comment)
        context = self.get_context_data()
        if form.is_valid():
            form.save()
            context['comment'] = self.updated_comment
            return render(request, 'comment/content.html', context)


class DeleteComment(BaseCommentView):
    def get(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if request.user != comment.user:
            raise PermissionDenied
        data = dict()
        context = self.get_context_data()
        context["comment"] = comment
        data['html_form'] = render_to_string('comment/comment_modal.html', context, request=request)
        return JsonResponse(data)

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if request.user != comment.user:
            raise PermissionDenied
        comment.delete()
        context = self.get_context_data()
        return render(request, 'comment/base.html', context)
