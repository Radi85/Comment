from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from comment.models import Comment
from comment.forms import CommentForm
from comment.utils import get_view_context, get_model_obj


@login_required(login_url='accounts:login')
def create_comment(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    if request.method == 'POST':
        form = CommentForm(request.POST)
        model_object = get_model_obj(request)

        if form.is_valid():
            # check and get the comment object if it is a parent
            parent_comment = None
            try:
                parent_id = int(request.POST.get("parent_id"))
            except:
                parent_id = None
            if parent_id:
                parent_qs = Comment.objects.filter(id=parent_id)
                if parent_qs.exists():
                    parent_comment = parent_qs.first()

            comment_content = form.cleaned_data['content']
            comment = Comment.objects.create(
                content_object=model_object,
                content=comment_content,
                user=request.user,
                parent=parent_comment,
            )
            # retrieve context dict after comment been created
            context = get_view_context(request)

            context['is_parent'] = not parent_comment
            if request.POST.get("commentform") == "reply":
                context['reply'] = comment
                return render(request, 'comment/child_comment.html', context)
            else:
                context['comment'] = comment
                return render(request, 'comment/base.html', context)


@login_required(login_url='accounts:login')
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    context = get_view_context(request)

    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    elif request.user != comment.user:
        raise PermissionDenied

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        context['commentform'] = form

        if form.is_valid():
            form.save()
            context['obj'] = comment
            context['is_parent'] = True
            # child comment
            if comment.parent:
                context['is_parent'] = False
            return render(request, 'comment/content.html', context)
    else:
        form = CommentForm(instance=comment)
        context['commentform'] = form
        context["comment"] = comment
        return render(request, 'comment/update_comment.html', context)


@login_required(login_url='accounts:login')
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    has_parent = False
    if comment.parent:
        has_parent = True

    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    elif request.user != comment.user:
        raise PermissionDenied

    if request.method == 'POST':
        comment.delete()
        # retrieve context dict after comment been deleted
        context = get_view_context(request)
        context["has_parent"] = has_parent
        return render(request, 'comment/base.html', context)
    else:
        data = dict()
        context = get_view_context(request)
        context["comment"] = comment
        context["has_parent"] = has_parent
        data['html_form'] = render_to_string(
            'comment/comment_modal.html',
            context,
            request=request,
        )
        return JsonResponse(data)
