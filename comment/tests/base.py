from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, RequestFactory

from comment.models import Comment, FlagInstance, Reaction, ReactionInstance
from test.example.post.models import Post


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
        self.moderator = user_model.objects.create_user(
            username="moderator",
            email="test-2@acme.edu",
            password="1234"
        )
        moderator_group = Group.objects.filter(name='comment_moderator').first()
        moderator_group.user_set.add(self.moderator)
        self.admin = user_model.objects.create_user(
            username="admin",
            email="test-2@acme.edu",
            password="1234"
        )
        admin_group = Group.objects.filter(name='comment_admin').first()
        admin_group.user_set.add(self.admin)

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
        self.reactions = 0
        self.flags = 0

    def create_comment(self, ct_object, parent=None):
        self.increment += 1
        return Comment.objects.create(
            content_object=ct_object,
            content='comment {}'.format(self.increment),
            user=self.user_1,
            parent=parent,
        )

    def create_reaction_instance(self, user, comment, reaction):
        reaction_type = getattr(ReactionInstance.ReactionType, reaction.upper(), None)
        if reaction_type:
            reaction_obj = Reaction.objects.get(comment=comment)
            self.reactions += 1
            reaction_instance = ReactionInstance.objects.create(
                user=user,
                reaction_type=reaction_type.value,
                reaction=reaction_obj
            )
            comment.reaction.refresh_from_db()
            return reaction_instance
        raise ValueError('{} is not a valid reaction type'.format(reaction))

    @staticmethod
    def set_reaction(user, comment, reaction):
        ReactionInstance.objects.set_reaction(user, comment.reaction, reaction)

    @staticmethod
    def set_flag(user, comment, **kwargs):
        return FlagInstance.objects.set_flag(user, comment.flag, **kwargs)

    def create_flag_instance(self, user, comment, **kwargs):
        instance = FlagInstance.objects.create(
            user=user,
            flag=comment.flag,
            **kwargs
        )
        self.flags += 1
        return instance


class BaseCommentManagerTest(BaseCommentTest):
    def setUp(self):
        super().setUp()
        self.parent_comment_1 = self.create_comment(self.content_object_1)
        self.parent_comment_2 = self.create_comment(self.content_object_1)
        self.parent_comment_3 = self.create_comment(self.content_object_1)
        self.child_comment_1 = self.create_comment(self.content_object_1, parent=self.parent_comment_1)
        self.child_comment_2 = self.create_comment(self.content_object_1, parent=self.parent_comment_2)
        self.child_comment_3 = self.create_comment(self.content_object_1, parent=self.parent_comment_2)

        self.parent_comment_4 = self.create_comment(self.content_object_2)
        self.parent_comment_5 = self.create_comment(self.content_object_2)
        self.child_comment_4 = self.create_comment(self.content_object_2, parent=self.parent_comment_1)
        self.child_comment_5 = self.create_comment(self.content_object_2, parent=self.parent_comment_2)


class BaseCommentFlagTest(BaseCommentTest):
    def setUp(self):
        super().setUp()
        self.comment = self.create_comment(self.content_object_1)
        self.user = self.user_1
        self.flag_data = {
            'reason': str(FlagInstance.objects.reason_values[0]),
            'info': None,
        }
        self.comment_2 = self.create_comment(self.content_object_2)
        self.flag_instance = self.create_flag_instance(self.user_2, self.comment_2, **self.flag_data)


class BaseTemplateTagsTest(BaseCommentTest):
    class MockUser:
        """Mock unauthenticated user for template. The User instance always returns True for `is_authenticated`"""
        is_authenticated = False

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        settings.PROFILE_APP_NAME = 'user_profile'
        self.parent_comment_1 = self.create_comment(self.content_object_1)
        self.parent_comment_2 = self.create_comment(self.content_object_1)
        self.parent_comment_3 = self.create_comment(self.content_object_1)
        self.child_comment_1 = self.create_comment(self.content_object_1, parent=self.parent_comment_1)
        self.child_comment_2 = self.create_comment(self.content_object_1, parent=self.parent_comment_2)
        self.child_comment_3 = self.create_comment(self.content_object_1, parent=self.parent_comment_2)
