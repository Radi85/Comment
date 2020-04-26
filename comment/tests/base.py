from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from test.example.post.models import Post
from comment.models import Comment


class BaseCommentTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user_1 = user_model.objects.create_user(
                    username="test-1",
                    email="test-1@acme.edu",
                    password="1234"
        )
        self.user_2 = user_model.objects.create_user(
            username="test-2",
            email="test-2@acme.edu",
            password="1234"
        )
        self.client.login(username='test-1', password='1234')
        self.post_1 = Post.objects.create(
            author=self.user_1,
            title="post 1",
            body="first post body"
        )
        self.post_2 = Post.objects.create(
            author=self.user_1,
            title="post 2",
            body="second post body"
        )
        content_type = ContentType.objects.get(model='post')
        self.content_object_1 = content_type.get_object_for_this_type(id=self.post_1.id)
        self.content_object_2 = content_type.get_object_for_this_type(id=self.post_2.id)
        self.increment = 0

    def create_comment(self, ct_object, parent=None):
        self.increment += 1
        return Comment.objects.create(
            content_object=ct_object,
            content='comment {}'.format(self.increment),
            user=self.user_1,
            parent=parent,
        )
