from django import forms
from django.utils.translation import gettext_lazy as _

from comment.models import Comment
from comment.conf import settings


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {'content': forms.Textarea(attrs={'rows': 1})}

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        if self.request.user.is_anonymous and settings.COMMENT_ALLOW_ANONYMOUS:
            self.fields['email'] = forms.EmailField(
                label=_("email"),
                widget=forms.EmailInput(attrs={
                    'placeholder': _('email address, this will be used for verification.'),
                    'title': _("email address, it will be used for verification.")
                    })
                )

    def clean_email(self):
        """this will only be executed when email field is present for unauthenticated users"""
        email = self.cleaned_data['email']
        return email.strip().lower()
