from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, RequestFactory, TransactionTestCase, Client
from django.utils import timezone

from comment.conf import settings
from comment.models import Comment, FlagInstance, Reaction, ReactionInstance
from post.models import Post


User = get_user_model()


class BaseCommentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user_1 = User.objects.create_user(
                    username="test-1",
                    email="test-1@acme.edu",
                    password="1234"
        )
        cls.user_2 = User.objects.create_user(
            username="test-2",
            email="test-2@acme.edu",
            password="1234"
        )
        cls.moderator = User.objects.create_user(
            username="moderator",
            email="test-2@acme.edu",
            password="1234"
        )
        moderator_group = Group.objects.filter(name='comment_moderator').first()
        moderator_group.user_set.add(cls.moderator)
        cls.admin = User.objects.create_user(
            username="admin",
            email="test-2@acme.edu",
            password="1234"
        )
        admin_group = Group.objects.filter(name='comment_admin').first()
        admin_group.user_set.add(cls.admin)
        cls.post_1 = Post.objects.create(
            author=cls.user_1,
            title="post 1",
            body="first post body"
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_1,
            title="post 2",
            body="second post body"
        )
        content_type = ContentType.objects.get(model='post')
        cls.content_object_1 = content_type.get_object_for_this_type(id=cls.post_1.id)
        cls.content_object_2 = content_type.get_object_for_this_type(id=cls.post_2.id)
        cls.increment = 0
        cls.reactions = 0
        cls.flags = 0

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)

    @classmethod
    def increase_comment_count(cls):
        cls.increment += 1

    @classmethod
    def create_comment(cls, ct_object, user=None, email=None, posted=None, parent=None):
        if not user:
            user = cls.user_1
        cls.increase_comment_count()
        return Comment.objects.create(
            content_object=ct_object,
            content='comment {}'.format(cls.increment),
            user=user,
            parent=parent,
        )

    @classmethod
    def create_anonymous_comment(cls, ct_object=None, email=None, posted=None, parent=None):
        if not ct_object:
            ct_object = cls.content_object_1
        if not email:
            email = cls.user_1.email
        if not posted:
            posted = timezone.now()
        cls.increase_comment_count()
        return Comment.objects.create(
            content_object=ct_object,
            content='anonymous comment {}'.format(cls.increment),
            parent=parent,
            email=email,
            posted=posted
        )

    @classmethod
    def create_reaction_instance(cls, user, comment, reaction):
        reaction_type = getattr(ReactionInstance.ReactionType, reaction.upper(), None)
        if reaction_type:
            reaction_obj = Reaction.objects.get(comment=comment)
            cls.reactions += 1
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

    @classmethod
    def create_flag_instance(cls, user, comment, **kwargs):
        instance = FlagInstance.objects.create(
            user=user,
            flag=comment.flag,
            **kwargs
        )
        cls.flags += 1
        return instance


class BaseCommentManagerTest(BaseCommentTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.parent_comment_1 = cls.create_comment(cls.content_object_1)
        cls.parent_comment_2 = cls.create_comment(cls.content_object_1)
        cls.parent_comment_3 = cls.create_comment(cls.content_object_1)
        cls.child_comment_1 = cls.create_comment(cls.content_object_1, parent=cls.parent_comment_1)
        cls.child_comment_2 = cls.create_comment(cls.content_object_1, parent=cls.parent_comment_2)
        cls.child_comment_3 = cls.create_comment(cls.content_object_1, parent=cls.parent_comment_2)

        cls.parent_comment_4 = cls.create_comment(cls.content_object_2)
        cls.parent_comment_5 = cls.create_comment(cls.content_object_2)
        cls.child_comment_4 = cls.create_comment(cls.content_object_2, parent=cls.parent_comment_1)
        cls.child_comment_5 = cls.create_comment(cls.content_object_2, parent=cls.parent_comment_2)


class BaseCommentViewTest(BaseCommentTest):

    def setUp(self):
        super().setUp()
        self.client = Client(HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client_non_ajax = Client()
        self.client.force_login(self.user_1)
        self.client_non_ajax.force_login(self.user_1)
        self.data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id,
        }


class BaseCommentFlagTest(BaseCommentViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_comment(cls.content_object_1)
        cls.user = cls.user_1
        cls.flag_data = {
            'reason': str(FlagInstance.objects.reason_values[0]),
            'info': None,
        }
        cls.comment_2 = cls.create_comment(cls.content_object_2)
        cls.flag_instance = cls.create_flag_instance(cls.user_2, cls.comment_2, **cls.flag_data)


class BaseTemplateTagsTest(BaseCommentTest):
    class MockUser:
        """Mock unauthenticated user for template. The User instance always returns True for `is_authenticated`"""
        is_authenticated = False

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.factory = RequestFactory()
        settings.PROFILE_APP_NAME = 'user_profile'
        settings.COMMENT_ALLOW_ANONYMOUS = True
        cls.increment = 0
        cls.parent_comment_1 = cls.create_comment(cls.content_object_1)
        cls.parent_comment_2 = cls.create_comment(cls.content_object_1)
        cls.parent_comment_3 = cls.create_comment(cls.content_object_1)
        cls.child_comment_1 = cls.create_comment(cls.content_object_1, parent=cls.parent_comment_1)
        cls.child_comment_2 = cls.create_comment(cls.content_object_1, parent=cls.parent_comment_2)
        cls.child_comment_3 = cls.create_comment(cls.content_object_1, parent=cls.parent_comment_2)
        cls.anonymous_parent_comment = cls.create_anonymous_comment()
        cls.anonymous_child_comment = cls.create_anonymous_comment(parent=cls.parent_comment_1)


class BaseCommentUtilsTest(BaseCommentTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.factory = RequestFactory()
        cls.comment_1 = cls.create_comment(cls.content_object_1)
        cls.comment_2 = cls.create_comment(cls.content_object_1)
        cls.comment_3 = cls.create_comment(cls.content_object_1)
        cls.anonymous_comment = cls.create_anonymous_comment()


class BaseCommentMigrationTest(TransactionTestCase):
    """
    Test specific migrations
        Make sure that `self.migrate_from` and `self.migrate_to` are defined.
    """

    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    migrate_from = None
    migrate_to = None

    def setUp(self):
        super().setUp()
        assert self.migrate_to and self.migrate_from, \
            f'TestCase {type(self).__name} must define migrate_to and migrate_from properties'
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        self.executor = MigrationExecutor(connection)
        self.old_apps = self.executor.loader.project_state(self.migrate_from).apps

        self.user = User.objects.create_user(username="tester-1")
        self.post = Post.objects.create(
            author=self.user,
            title="post 3",
            body="third post body"
        )
        content_type = ContentType.objects.get(model='post')
        self.ct_object = content_type.get_object_for_this_type(id=self.post.id)

        # revert to the original migration
        self.executor.migrate(self.migrate_from)
        # ensure return to the latest migration, even if the test fails
        self.addCleanup(self.force_migrate)

        self.setUpBeforeMigration(self.old_apps)
        self.executor.loader.build_graph()
        self.executor.migrate(self.migrate_to)
        self.new_apps = self.executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass

    @property
    def new_model(self):
        return self.new_apps.get_model(self.app, 'Comment')

    @property
    def old_model(self):
        return self.old_apps.get_model(self.app, 'Comment')

    def force_migrate(self, migrate_to=None):
        self.executor.loader.build_graph()  # reload.
        if migrate_to is None:
            # get latest migration of current app
            migrate_to = [key for key in self.executor.loader.graph.leaf_nodes() if key[0] == self.app]
        self.executor.migrate(migrate_to)


class BaseCommentMixinTest(BaseCommentTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.factory = RequestFactory()
        cls.url_data = {
            'model_name': 'post',
            'app_name': 'post',
            'model_id': 1
        }

    def get_url(self, base_url=None, **kwargs):
        if not base_url:
            base_url = self.base_url
        if kwargs:
            base_url += '?'
            for (key, val) in kwargs.items():
                base_url += str(key) + '=' + str(val) + '&'
        return base_url.rstrip('&')


class BaseCommentSignalTest(BaseCommentManagerTest):
    def setUp(self):
        super().setUp()
        self.user = self.user_1
        self.comment = self.child_comment_1
        self.LIKE = ReactionInstance.ReactionType.LIKE
        self.DISLIKE = ReactionInstance.ReactionType.DISLIKE
        self.flag_data = {
            'reason': str(FlagInstance.objects.reason_values[0]),
            'info': None,
        }
