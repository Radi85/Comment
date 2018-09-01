from django.contrib import admin
from comment.models import Comment


class CommentModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'posted_date', 'content_type', 'user')
    search_fields = ('content',)
    class Meta:
        model = Comment

admin.site.register(Comment, CommentModelAdmin)
