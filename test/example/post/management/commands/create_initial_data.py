from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand

from comment.models import Comment
from post.models import Post


class Command(BaseCommand):
    help = "Generate initial data"

    def handle(self, *args, **options):
        generate_initial_data()


def get_or_create(username, password):
    created = False
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(username=username, password=password)
        created = True
    return user, created


def generate_initial_data():
    admin, created = get_or_create('admin', password='admin')
    if created:
        admin_group, _ = Group.objects.get_or_create(name='comment_admin')
        admin_group.user_set.add(admin)

    moderator, created = get_or_create('moderator', password='moderator')
    if created:
        moderator_group, _ = Group.objects.get_or_create(name='comment_moderator')
        moderator_group.user_set.add(moderator)

    normal_user, _ = get_or_create('test', password='test')

    try:
        Post.objects.get(title='Test Post')
    except Post.DoesNotExist:
        post = Post.objects.create(title='Test Post', body='Hello django comments dab', author=normal_user)
        comment_1 = Comment.objects.create(content='First comment', user=moderator, content_object=post)
        Comment.objects.create(
            content='Reply comment',
            user=normal_user,
            content_object=post,
            parent=comment_1
        )
        Comment.objects.create(content='Second comment', user=admin, content_object=post)
