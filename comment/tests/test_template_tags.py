from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateSyntaxError

from comment.conf import settings
from comment.forms import CommentForm
from comment.managers import FlagInstanceManager
from comment.templatetags.comment_tags import (
    get_model_name, get_app_name, get_comments_count, get_img_path, get_profile_url, render_comments,
    include_bootstrap, include_static, render_field, has_reacted, has_flagged,
    render_flag_reasons, render_content, get_username_for_comment)
from comment.tests.base import BaseTemplateTagsTest


class CommentTemplateTagsTest(BaseTemplateTagsTest):
    def test_get_model_name(self):
        model_name = get_model_name(self.post_1)
        self.assertEqual(model_name, 'Post')

    def test_get_app_name(self):
        app_name = get_app_name(self.post_1)
        self.assertEqual(app_name, 'post')

    def test_comments_count(self):
        counts = get_comments_count(self.post_1, self.user_1)
        self.assertEqual(counts, self.increment)

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
    def test_get_profile_url(self):
        # profile exist
        url = get_profile_url(self.parent_comment_1)
        self.assertEqual(url, '/profile/profile/test-1')

        # anonymous comment
        url = get_profile_url(self.anonymous_parent_comment)
        self.assertEqual(url, '/static/img/default.png')

        # missing profile
        with patch.object(settings, 'PROFILE_MODEL_NAME', None):
            url = get_profile_url(self.parent_comment_1)
            self.assertEqual(url, '/static/img/default.png')

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
    def test_get_img_path(self):
        url = get_img_path(self.parent_comment_1)
        self.assertNotEqual(url, '/static/img/default.png')

        # use default pic on fail
        with patch.object(settings, 'PROFILE_MODEL_NAME', 'app not exist'):
            url = get_img_path(self.parent_comment_1)
            self.assertEqual(url, '/static/img/default.png')

        with patch.object(settings, 'PROFILE_APP_NAME', 'user_profile'):
            with patch('comment.templatetags.comment_tags.get_profile_instance', return_value=None):
                url = get_img_path(self.parent_comment_1)
                self.assertEqual(url, '/static/img/default.png')

    @patch.object(settings, 'PROFILE_APP_NAME', 'user_profile')
    @patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
    def test_profile_has_no_image_field(self):
        with patch('comment.templatetags.comment_tags.hasattr', return_value=False):
            url = get_img_path(self.parent_comment_1)
            self.assertEqual(url, '/static/img/default.png')

    def test_render_comments(self):
        request = self.factory.get('/')
        request.user = self.user_1
        comments_per_page = 'COMMENT_PER_PAGE'
        patch.object(settings, comments_per_page, 0).start()
        count = self.post_1.comments.filter_parents_by_object(self.post_1).count()
        data = render_comments(self.post_1, request)

        # no pagination
        self.assertEqual(data['comments'].count(), count)  # parent comment only
        self.assertEqual(data['login_url'], settings.LOGIN_URL)

    @patch.object(settings, 'LOGIN_URL', None)
    def test_render_comments_without_login_url(self):
        request = self.factory.get('/')
        request.user = self.user_1
        with self.assertRaises(ImproperlyConfigured) as error:
            render_comments(self.post_1, request)
        self.assertIsInstance(error.exception, ImproperlyConfigured)

    @patch.object(settings, 'COMMENT_PER_PAGE', 2)
    def test_render_comments_with_pagination(self):
        request = self.factory.get('/?page=2')
        request.user = self.user_1
        data = render_comments(self.post_1, request)

        self.assertIs(data['comments'].has_previous(), True)
        self.assertEqual(data['comments'].paginator.per_page, 2)  # 2 comment per page
        self.assertEqual(data['comments'].number, 2)  # 3 comment fit in 2 pages
        self.assertEqual(data['login_url'], settings.LOGIN_URL)

        # check not integer page
        request = self.factory.get('/?page=string')
        request.user = self.user_1
        data = render_comments(self.post_1, request)
        self.assertIs(data['comments'].has_previous(), False)

        # check empty page
        request = self.factory.get('/?page=10')
        request.user = self.user_1
        data = render_comments(self.post_1, request)
        self.assertIs(data['comments'].has_previous(), True)

    def test_static_functions(self):
        self.assertEqual(include_static(), '')
        self.assertIsNone(include_bootstrap())

    def test_render_field(self):
        request = self.factory.get('/')
        request.user = self.user_1
        form = CommentForm(request=request)
        for field in form.visible_fields():
            self.assertIsNone(field.field.widget.attrs.get('placeholder'))
            field = render_field(field, placeholder='placeholder')
            self.assertEqual(field.field.widget.attrs.get('placeholder'), 'placeholder')

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', 10)
    def test_render_content(self):
        comment = self.parent_comment_1
        content = "Any long text just for testing render content function"
        comment.content = content
        comment.save()
        content_words = comment.content.split()
        self.assertEqual(len(content_words), len(content.split()))

        result = render_content(comment)
        # test urlhash
        self.assertEqual(result['urlhash'], comment.urlhash)
        # truncate number is bigger than content words
        self.assertEqual(result['text_1'], comment.content)
        self.assertIsNone(result['text_2'])

    def test_single_line_breaks_in_render_content(self):
        comment = self.parent_comment_1
        comment.content = "Any long text\njust for testing render\ncontent function"

        result = render_content(comment)

        self.assertIn('<br>', result['text_1'])
        self.assertNotIn('<br><br>', result['text_1'])

    def test_multiple_line_breaks_in_render_content(self):
        comment = self.parent_comment_1
        comment.content = "Any long text\n\njust for testing render\n\n\ncontent function"

        result = render_content(comment)

        self.assertIn('<br><br>', result['text_1'])
        self.assertNotIn('<br><br><br>', result['text_1'])

    def test_render_content_with_passing_value(self):
        comment = self.parent_comment_1
        content = "Any long text just for testing render content function"
        comment.content = content
        comment.save()
        content_words = comment.content.split()
        self.assertEqual(len(content_words), len(content.split()))

        result = render_content(comment, 5)
        # test urlhash
        self.assertEqual(result['urlhash'], comment.urlhash)
        # truncate number is smaller than content words
        self.assertEqual(result['text_1'], ' '.join(content_words[:5]))
        self.assertEqual(result['text_2'], ' '.join(content_words[5:]))

    @patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', True)
    def test_get_username_for_comment_use_email_first_part_enabled(self):
        comment = self.create_comment(self.content_object_1, user=self.user_1)

        self.assertEqual(get_username_for_comment(comment), comment.user.username)

        # test for anonymous
        anonymous_comment = self.create_anonymous_comment()

        self.assertEqual(get_username_for_comment(anonymous_comment), anonymous_comment.email.split('@')[0])

    @patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', False)
    def test_get_username_for_comment_use_email_first_part_disabled(self):
        comment = self.create_comment(self.content_object_1, user=self.user_1)

        self.assertEqual(get_username_for_comment(comment), comment.user.username)

        # test for anonymous
        anonymous_comment = self.create_anonymous_comment()

        self.assertEqual(get_username_for_comment(anonymous_comment), settings.COMMENT_ANONYMOUS_USERNAME)


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
