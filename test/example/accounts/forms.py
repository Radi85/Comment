from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.admin import widgets
from accounts.models import UserProfile



class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.username = self.cleaned_data.get('username')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user

    def clean_email(self):
        # Get the email
        email = self.cleaned_data.get('email')
        # Check to see if any users already exist with this email as a username.
        try:
            match = User.objects.get(email=email)
        except User.DoesNotExist:
            # Unable to find a user, this is fine
            return email
        # A user was found with this as a username, raise an error.
        raise forms.ValidationError('This email address is already exist.')


