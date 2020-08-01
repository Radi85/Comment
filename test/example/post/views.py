from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.decorators import login_required

from .models import Post
from .forms import PostForm


class PostListView(ListView):
    model = Post
    template_name = 'post/postlist.html'
    paginate_by = 10


class PostDetailView(DetailView):
    model = Post
    template_name = 'post/postdetail.html'


@login_required(login_url='profile:login')
def createpost_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # save the user who created the post
            post.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm
    context = {'form': form}
    return render(request, 'post/createpost.html', context)
