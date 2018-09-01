from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from comment.models import Comment
from comment.forms import CommentForm


@login_required(login_url='accounts:login')
def create_comment(request):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        context = {'commentform': form}
        try:
            context['profile_app_name'] = request.POST['profile_app_name']
            context['profile_model_name'] = request.POST['profile_model_name']
        except KeyError:
            pass
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
            content_type = ContentType.objects.get(
                app_label=request.POST['app_name'],
                model=request.POST['model'].lower()
            )
            model_object = content_type.get_object_for_this_type(
                id=request.POST['model_id']
            )
            comment = Comment.objects.create(
                content_object=model_object,
                content=comment_content,
                user=request.user,
                parent=parent_comment,
            )
            context['is_parent'] = not parent_comment
            if request.POST.get("commentform") == "reply":
                context['reply'] = comment
                return render(request, 'comment/child_comment.html', context)
            else:
                context['comment'] = comment
                context['model_object'] = model_object
                return render(request, 'comment/parent_comment.html', context)


@login_required(login_url='accounts:login')
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    elif request.user != comment.user:
        return redirect('accounts:profile', username=request.user.username)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        context = {'commentform': form}
        try:
            context['profile_app_name'] = request.POST['profile_app_name']
            context['profile_model_name'] = request.POST['profile_model_name']
        except KeyError:
            pass
        if form.is_valid():
            form.save()
            context['obj'] = comment
            context['is_parent'] = True
            # child comment
            if comment.parent:
                context['is_parent'] = False
            return render(request, 'comment/update_done.html', context)
    else:
        form = CommentForm(instance=comment)
        context = {'comment': comment, 'commentform': form}
        try:
            context['profile_app_name'] = request.GET['profile_app_name']
            context['profile_model_name'] = request.GET['profile_model_name']
        except KeyError:
            pass
        return render(request, 'comment/update_comment.html', context)


@login_required(login_url='accounts:login')
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    data = dict()
    has_parent = False
    if comment.parent:
        has_parent = True

    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    elif request.user != comment.user:
        return redirect('accounts:profile', username=request.user.username)

    count = comment.replies.count()
    if request.method == 'POST':
        comment.delete()
        data = {"count": count, "hasParent": has_parent}
        return JsonResponse(data)
    else:
        context = {'comment': comment,}
        data['html_form'] = render_to_string(
            'comment/comment_modal.html',
            context,
            request=request,
        )
        return JsonResponse(data)
