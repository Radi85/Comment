from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import login
from django.contrib.auth.models import User
from accounts.forms import SignupForm


def signup_view(request):
    if request.method == 'POST':
        signupform = SignupForm(request.POST)
        if signupform.is_valid():      
            user = signupform.save()
            login(request, user)
            return redirect('post:postlist')
    else:
        signupform = SignupForm()
    context = {'form': signupform}
    return render(request, 'accounts/signup.html', context)


def user_profile(request, username):
    viewed_user = get_object_or_404(User, username=username)
    context = locals()
    return render(request, 'accounts/profile.html', context)
