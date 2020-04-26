from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from .forms import SignupForm


def signup_view(request):
    if request.method == 'POST':
        signup_form = SignupForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save()
            login(request, user)
            return redirect('post:postlist')
    else:
        signup_form = SignupForm()
    context = {'form': signup_form}
    return render(request, 'accounts/signup.html', context)


def user_profile(request, username):
    viewed_user = get_object_or_404(User, username=username)
    context = locals()
    return render(request, 'accounts/profile.html', context)
