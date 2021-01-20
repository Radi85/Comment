from urllib.parse import quote_plus
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, RequestFactory, TransactionTestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone, translation
from lxml.html.soupparser import fromstring
from lxml.cssselect import CSSSelector

from comment.conf import settings
from comment.models import Comment, FlagInstance, Reaction, ReactionInstance
from post.models import Post


User = get_user_model()


@patch.object(settings, 'COMMENT_ALLOW_TRANSLATION', True)
class BaseInternationalizationTest:
    translatable_attrs = ['title', 'aria-label']

    @staticmethod
    def has_translatable_html_text(element):
        if "comment-translatable" in element.attrib.get('class', '').split():
            return True
        return False

    @staticmethod
    def has_translatable_html_attr(element, attr):
        if element.attrib.get(attr, '').strip():
            return True
        return False

    @staticmethod
    def is_translated(text):
        try:
            text.encode('ascii')
        except UnicodeEncodeError:
            return True
        return False

    @staticmethod
    def get_view_from_url_or_none(url):
        if url:
            clean_url = url.split('?')[0]
            return resolve(clean_url)[0].__name__


class BaseCommentTest(TestCase, BaseInternationalizationTest):
    flags = 0
    reactions = 0
    content_object_1 = None
    increment = 0
    user_1 = None

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
        cls.user_without_email = User.objects.create_user(
            username="no-email",
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
        translation.activate("test")
        self.addCleanup(patch.stopall)

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

    def _check_translatable_html_text(self, element, url):
        if self.has_translatable_html_text(element):
            self.assertTrue(
                self.is_translated(element.text),
                (f'No translation for the element {element.tag} with text "{element.text}" '
                 f'from view {self.get_view_from_url_or_none(url)}')
            )

    def _check_translatable_html_attrs(self, element, url):
        for attr in self.translatable_attrs:
            if self.has_translatable_html_attr(element, attr):
                self.assertTrue(
                    self.is_translated(element.attrib.get(attr)),
                    (f'No translation for the attribute "{attr}" of the element {element.tag} with the '
                     f'value "{element.attrib.get(attr)}" from view {self.get_view_from_url_or_none(url)}')
                )

    def assertHtmlTranslated(self, html, url=None):
        root = fromstring(html)
        sel = CSSSelector('*')

        for element in sel(root):
            self._check_translatable_html_text(element, url)
            self._check_translatable_html_attrs(element, url)

    def assertTextTranslated(self, text, url=None):
        self.assertTrue(
            self.is_translated(text),
            f'No translation for the text "{text}" from view {self.get_view_from_url_or_none(url)}'
        )

    def assertQuerysetEqual(self, qs, values, transform=None, ordered=True, msg=None):
        if not transform:
            def transform(x):
                return x
        return super().assertQuerysetEqual(qs, values, transform=transform, ordered=True, msg=msg)


class BaseCommentManagerTest(BaseCommentTest):
    content_object_2 = None

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
        self.client.force_login(self.user_2)
        self.client_non_ajax.force_login(self.user_2)
        self.data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id,
        }

    @staticmethod
    def get_url(reverse_name, pk=None, data=None):
        if pk:
            url = reverse(reverse_name, args=[pk])
        else:
            url = reverse(reverse_name)

        if not data:
            data = {}

        query_string = '&'.join([f'{name}={quote_plus(str(value))}' for name, value in data.items()])
        if query_string:
            return url + f'?{query_string}'
        return url


class BaseCommentFlagTest(BaseCommentViewTest):
    user_2 = None
    content_object_2 = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_comment(cls.content_object_1)
        cls.comment_for_change_state = cls.create_comment(cls.content_object_1)
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
    base_url = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.factory = RequestFactory()
        cls.data = {
            'content': 'test',
            'model_name': 'post',
            'app_name': 'post',
            'model_id': 1
        }
        cls.comment = cls.create_comment(cls.post_1, cls.user_1)

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
