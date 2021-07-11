from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateSyntaxError
from django.test import SimpleTestCase

from comment.conf import settings
from comment.forms import CommentForm
from comment.managers import FlagInstanceManager
from comment.templatetags.comment_tags import (
    get_model_name, get_app_name, get_comments_count, get_img_path, get_profile_url, render_comments,
    include_bootstrap, include_static, render_field, has_reacted, has_flagged,
    render_flag_reasons, render_content, get_username_for_comment, can_block_users_tag, is_user_blocked
)
from comment.tests.base import BaseTemplateTagsTest


class GetModelNameTest(BaseTemplateTagsTest):
    def test_success(self):
        model_name = get_model_name(self.post_1)
        self.assertEqual(model_name, 'Post')


class GetAppNameTest(BaseTemplateTagsTest):
    def test_success(self):
        app_name = get_app_name(self.post_1)
        self.assertEqual(app_name, 'post')


class GetCommentCountTest(BaseTemplateTagsTest):
    def test_success(self):
        counts = get_comments_count(self.post_1, self.user_1)
        self.assertEqual(counts, self.increment)


@patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
class GetProfileURLTest(BaseTemplateTagsTest):
    def test_profile_exists(self):
        url = get_profile_url(self.parent_comment_1)
        self.assertEqual(url, '/profile/profile/test-1')

    def test_anonymous_comment(self):
        url = get_profile_url(self.anonymous_parent_comment)
        self.assertEqual(url, '/static/img/default.png')

    @patch.object(settings, 'PROFILE_MODEL_NAME', None)
    def test_profile_does_not_exist(self):
        url = get_profile_url(self.parent_comment_1)
        self.assertEqual(url, '/static/img/default.png')


@patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
class GetImgPathTest(BaseTemplateTagsTest):
    def test_get_img_path(self):
        url = get_img_path(self.parent_comment_1)
        self.assertNotEqual(url, '/static/img/default.png')

    @patch.object(settings, 'PROFILE_MODEL_NAME', 'app not exist')
    def test_profile_is_not_found(self):
        url = get_img_path(self.parent_comment_1)
        self.assertEqual(url, settings.COMMENT_DEFAULT_PROFILE_PIC_LOC)

    @patch.object(settings, 'PROFILE_APP_NAME', 'user_profile')
    def test_profile_with_image(self):
        with patch('comment.templatetags.comment_tags.get_profile_instance', return_value=None):
            url = get_img_path(self.parent_comment_1)
            self.assertEqual(url, '/static/img/default.png')

    @patch.object(settings, 'PROFILE_APP_NAME', 'user_profile')
    @patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
    def test_profile_has_no_image_field(self):
        with patch('comment.templatetags.comment_tags.hasattr', return_value=False):
            url = get_img_path(self.parent_comment_1)
            self.assertEqual(url, '/static/img/default.png')


class RenderCommentsTest(BaseTemplateTagsTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.request = cls.factory.get('/')
        cls.request.user = cls.user_1

    @patch.object(settings, 'COMMENT_PER_PAGE', 0)
    def test_without_pagination(self):
        count = self.post_1.comments.filter_parents_by_object(self.post_1).count()
        data = render_comments(self.post_1, self.request)

        self.assertEqual(data['comments'].count(), count)  # parent comment only
        self.assertEqual(data['login_url'], settings.LOGIN_URL)
        # check if `request` object is passed in context template
        self.assertEqual(data['request'], self.request)

    @patch.object(settings, 'LOGIN_URL', None)
    def test_without_login_url(self):
        with self.assertRaises(ImproperlyConfigured) as error:
            render_comments(self.post_1, self.request)
        self.assertIsInstance(error.exception, ImproperlyConfigured)

    @patch.object(settings, 'COMMENT_PER_PAGE', 2)
    def test_with_pagination(self):
        request = self.factory.get('/?page=2')
        request.user = self.user_1
        data = render_comments(self.post_1, request)

        self.assertIs(data['comments'].has_previous(), True)
        self.assertEqual(data['comments'].paginator.per_page, 2)  # 2 comment per page
        self.assertEqual(data['comments'].number, 2)  # 3 comment fit in 2 pages
        self.assertEqual(data['login_url'], settings.LOGIN_URL)

    def test_non_integral_page_number(self):
        request = self.factory.get('/?page=string')
        request.user = self.user_1
        data = render_comments(self.post_1, request)
        self.assertIs(data['comments'].has_previous(), False)

    @patch.object(settings, 'COMMENT_PER_PAGE', 2)
    def test_empty_page(self):
        request = self.factory.get('/?page=10')
        request.user = self.user_1
        data = render_comments(self.post_1, request)
        self.assertIs(data['comments'].has_previous(), True)


class TestStaticFunctions(SimpleTestCase):
    def test_include_static(self):
        msg = (
            'The tag `include_static` has been deprecated. Static files are now rendered implicitly.'
            'You can remove this from your django template. This tag will be removed in v3.0.0.'
        )
        with self.assertWarnsMessage(DeprecationWarning, msg):
            self.assertEqual(include_static(), '')

    def test_include_bootstrap(self):
        self.assertIsNone(include_bootstrap())


class RenderFieldTest(BaseTemplateTagsTest):
    def test_success(self):
        request = self.factory.get('/')
        request.user = self.user_1
        form = CommentForm(request=request)
        for field in form.visible_fields():
            self.assertIsNone(field.field.widget.attrs.get('placeholder'))
            field = render_field(field, placeholder='placeholder')
            self.assertEqual(field.field.widget.attrs.get('placeholder'), 'placeholder')


class RenderContentTest(BaseTemplateTagsTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.parent_comment_1
        cls.content = "Any long text just for testing render content function"
        cls.comment.content = cls.content
        cls.comment.save()

    def setUp(self):
        super().setUp()
        self.comment.refresh_from_db()

    def test_urlhash(self):
        result = render_content(self.comment)
        self.assertEqual(result['urlhash'], self.comment.urlhash)

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', 20)
    def test_content_wrapping_with_large_truncate_number(self):
        content_words = self.comment.content.split()
        self.assertIs(len(content_words) < 20, True)

        result = render_content(self.comment)

        self.assertEqual(result['text_1'], self.comment.content)
        self.assertIsNone(result['text_2'])

    def test_single_line_breaks(self):
        comment = self.parent_comment_1
        comment.content = "Any long text\njust for testing render\ncontent function"
        comment.save()
        comment.refresh_from_db()

        result = render_content(comment)

        self.assertIn('<br>', result['text_1'])
        self.assertNotIn('<br><br>', result['text_1'])

    def test_multiple_line_breaks(self):
        comment = self.parent_comment_1
        comment.content = "Any long text\n\njust for testing render\n\n\ncontent function"
        comment.save()
        comment.refresh_from_db()

        result = render_content(comment)

        self.assertIn('<br><br>', result['text_1'])
        self.assertNotIn('<br><br><br>', result['text_1'])

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', 5)
    def test_content_wrapping_with_small_truncate_number(self):
        self.comment.refresh_from_db()
        content_words = self.comment.content.split()
        self.assertEqual(len(content_words), len(self.content.split()))

        result = render_content(self.comment)

        # truncate number is smaller than words in content
        self.assertEqual(result['text_1'], ' '.join(content_words[:5]))
        self.assertEqual(result['text_2'], ' '.join(content_words[5:]))


class GetUsernameForCommentTest(BaseTemplateTagsTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_comment(cls.content_object_1, user=cls.user_1)
        cls.anonymous_comment = cls.create_anonymous_comment()

    @patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', True)
    def test_use_email_first_part_enabled(self):
        self.assertEqual(get_username_for_comment(self.comment), self.comment.user.username)

        # test for anonymous
        self.assertEqual(get_username_for_comment(self.anonymous_comment), self.anonymous_comment.email.split('@')[0])

    @patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', False)
    def test_use_email_first_part_disabled(self):
        self.assertEqual(get_username_for_comment(self.comment), self.comment.user.username)

        # test for anonymous
        self.assertEqual(get_username_for_comment(self.anonymous_comment), settings.COMMENT_ANONYMOUS_USERNAME)


class ReactionTemplateTagsTest(BaseTemplateTagsTest):
    def setUp(self):
        super().setUp()
        self.comment = self.create_comment(self.content_object_1)
        self.user = self.user_1
        self.reaction = self.create_reaction_instance(self.user, self.comment, 'like')

    def test_has_reacted_for_unauthenticated_user(self):
        """Test whether the filter returns False for unauthenticated users"""
        user = self.MockUser()
        self.assertEqual(False, has_reacted(self.comment, user, 'like'))

    def test_has_reacted_on_incorrect_reaction(self):
        """Test whether this function raises an error when incorrect reaction is passed"""
        self.assertRaises(TemplateSyntaxError, has_reacted, self.comment, self.user, 'likes')

    def test_has_reacted_on_correct_reaction_for_authenticated_users(self):
        """Test whether this function returns an appropriate boolean when correct reaction is passed"""
        comment = self.comment
        user = self.user

        self.assertEqual(True, has_reacted(comment, user, 'like'))
        self.assertEqual(False, has_reacted(comment, user, 'dislike'))

        # check for other users
        user = self.user_2

        self.assertEqual(False, has_reacted(comment, user, 'like'))
        self.assertEqual(False, has_reacted(comment, user, 'dislike'))

        # check for other comments
        self.assertEqual(False, has_reacted(comment, user, 'like'))
        self.assertEqual(False, has_reacted(comment, user, 'dislike'))


class CommentFlagTemplateTagsTest(BaseTemplateTagsTest):
    def setUp(self):
        super().setUp()
        self.comment = self.create_comment(self.content_object_1)
        self.user = self.user_1
        self.flag = self.create_flag_instance(self.user, self.comment)

    def test_has_flagged_for_unauthenticated_user(self):
        user = self.MockUser()
        self.assertEqual(False, has_flagged(user, self.parent_comment_1))

    def test_has_flagged_for_unflagged_comment(self):
        self.assertEqual(False, has_flagged(self.user_2, self.comment))

    def test_has_flagged_for_flagged_comment(self):
        self.assertEqual(True, has_flagged(self.user, self.comment))

    def test_render_flag_reasons(self):
        self.assertListEqual(FlagInstanceManager.reasons_list, render_flag_reasons())


class BlockingTagsTest(BaseTemplateTagsTest):

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_admin_can_block_users(self):
        self.assertTrue(can_block_users_tag(self.admin))

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_normal_user_cannot_block_users(self):
        self.assertTrue(can_block_users_tag(self.admin))

    @patch('comment.managers.BlockedUserManager.is_user_blocked', return_value=True)
    def test_blocked_user(self, _):
        self.assertTrue(is_user_blocked(self.parent_comment_1))

    @patch('comment.managers.BlockedUserManager.is_user_blocked', return_value=False)
    def test_unblocked_user(self, _):
        self.assertFalse(is_user_blocked(self.parent_comment_1))
