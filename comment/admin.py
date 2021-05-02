from django.contrib import admin

from comment.models import (
    Comment, Flag, FlagInstance, Reaction, ReactionInstance, Follower, BlockedUser, BlockedUserHistory
)


class CommentModelAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'posted', 'edited', 'content_type', 'user', 'email', 'urlhash')
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


class InlineFlagInstance(admin.TabularInline):
    model = FlagInstance
    extra = 0
    readonly_fields = ['user', 'flag', 'reason', 'info', 'date_flagged']


class FlagModelAdmin(admin.ModelAdmin):
    list_display = ('comment', 'moderator', 'state', 'count', 'comment_author')
    readonly_fields = list_display
    search_fields = ('comment__content',)
    inlines = [InlineFlagInstance]


class FollowerModelAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'content_type', 'content_object')
    readonly_fields = list_display
    search_fields = ('email',)


class BlockedUserModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'blocked')
    search_fields = ('user__username', 'email')


class BlockedUserHistoryModelAdmin(admin.ModelAdmin):
    list_display = ('blocked_user', 'blocker', 'reason', 'state', 'date')
    search_fields = (
        'blocked_user__user__username', 'blocked_user__email', 'blocker__username', 'blocker__email', 'state',  'date'
    )


admin.site.register(Comment, CommentModelAdmin)
admin.site.register(Reaction, ReactionModelAdmin)
admin.site.register(Flag, FlagModelAdmin)
admin.site.register(Follower, FollowerModelAdmin)
admin.site.register(BlockedUser, BlockedUserModelAdmin)
admin.site.register(BlockedUserHistory, BlockedUserHistoryModelAdmin)
