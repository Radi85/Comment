from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from comment.conf import settings
from comment.models import Comment


def create_permission_groups(sender, **kwargs):
    if settings.COMMENT_FLAGS_ALLOWED or settings.COMMENT_ALLOW_BLOCKING_USERS:
        comment_ct = ContentType.objects.get_for_model(Comment)
        delete_comment_perm, __ = Permission.objects.get_or_create(
            codename='delete_comment',
            name='Can delete comment',
            content_type=comment_ct
        )
        admin_group, __ = Group.objects.get_or_create(name='comment_admin')
        admin_group.permissions.add(delete_comment_perm)
        delete_flagged_comment_perm, __ = Permission.objects.get_or_create(
            codename='delete_flagged_comment',
            name='Can delete flagged comment',
            content_type=comment_ct
        )
        moderator_group, __ = Group.objects.get_or_create(name='comment_moderator')
        moderator_group.permissions.add(delete_flagged_comment_perm)
        admin_group.permissions.add(delete_flagged_comment_perm)


def adjust_flagged_comments(sender, **kwargs):
    [
        comment.flag.toggle_flagged_state()
        for comment in Comment.objects.all()
    ]
