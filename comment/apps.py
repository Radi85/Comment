from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def create_permission_groups(sender, **kwargs):
    from django.contrib.auth.models import Permission, Group
    from django.contrib.contenttypes.models import ContentType
    from comment.models import Comment

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
    from comment.models import Comment
    for comment in Comment.objects.all():
        comment.flag.toggle_flagged_state()


class CommentConfig(AppConfig):
    name = 'comment'
    verbose_name = _('comment')

    def ready(self):
        post_migrate.connect(create_permission_groups, sender=self)
        post_migrate.connect(adjust_flagged_comments, sender=self)
