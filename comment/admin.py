from django.contrib import admin

from comment.models import Comment, Reaction, ReactionInstance


class CommentModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'posted', 'edited', 'content_type', 'user')
    search_fields = ('content',)

    class Meta:
        model = Comment


class InlineReactionInstance(admin.TabularInline):
    model = ReactionInstance
    extra = 0
    readonly_fields = ['user', 'reaction', 'reaction_type', 'date_reacted']


class ReactionModelAdmin(admin.ModelAdmin):
    list_display = ('comment', 'likes', 'dislikes')
    readonly_fields = list_display
    search_fields = ('comment__content',)
    inlines = [InlineReactionInstance]


admin.site.register(Comment, CommentModelAdmin)
admin.site.register(Reaction, ReactionModelAdmin)
