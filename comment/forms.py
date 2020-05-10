from django import forms

from comment.models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content', )
        widgets = {'content': forms.Textarea(attrs={'rows': 1})}
