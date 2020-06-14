from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.template import TemplateSyntaxError

from comment.forms import CommentForm
from comment.managers import FlagInstanceManager
from comment.templatetags.comment_tags import (
    get_model_name, get_app_name, get_comments_count, get_img_path, get_profile_url, render_comments,
    include_static_jquery, include_bootstrap, include_static, render_field, has_reacted, has_flagged,
    render_flag_reasons,
    render_content)
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
        self.assertEqual(counts, 6)

    def test_profile_url(self):
        # success
        url = get_profile_url(self.parent_comment_1)
        self.assertEqual(url, '/profile/profile/test-1')
        # fail
        settings.PROFILE_APP_NAME = 'app not exist'
        url = get_profile_url(self.parent_comment_1)
        self.assertEqual(url, '')

        settings.PROFILE_APP_NAME = None
        url = get_profile_url(self.parent_comment_1)
        self.assertEqual(url, '')

    def test_img_url(self):
        url = get_img_path(self.parent_comment_1)
        self.assertNotEqual(url, '')
        # fail
        settings.PROFILE_APP_NAME = 'app not exist'
        url = get_img_path(self.parent_comment_1)
        self.assertEqual(url, '')

        settings.PROFILE_APP_NAME = None
        url = get_img_path(self.parent_comment_1)
        self.assertEqual(url, '')

    def test_profile_has_no_image_field(self):
        mocked_hasattr = patch('comment.templatetags.comment_tags.hasattr').start()
        mocked_hasattr.return_value = False
        url = get_img_path(self.parent_comment_1)
        self.assertEqual(url, '')

    def test_render_comments(self):
        request = self.factory.get('/')
        request.user = self.user_1
        data = render_comments(self.post_1, request, comments_per_page=None)
        self.assertEqual(data['comments'].count(), 3)  # parent comment only
        self.assertEqual(data['login_url'], '/' + settings.LOGIN_URL)

        # LOGIN_URL is not provided
        setattr(settings, 'LOGIN_URL', None)
        with self.assertRaises(ImproperlyConfigured) as error:
            render_comments(self.post_1, request)
        self.assertIsInstance(error.exception, ImproperlyConfigured)

        # check pagination
        setattr(settings, 'LOGIN_URL', '/login')
        request = self.factory.get('/?page=2')
        request.user = self.user_1
        data = render_comments(self.post_1, request, comments_per_page=2)
        self.assertTrue(data['comments'].has_previous())
        self.assertEqual(data['comments'].paginator.per_page, 2)  # 2 comment per page
        self.assertEqual(data['comments'].number, 2)  # 3 comment fit in 2 pages
        self.assertEqual(data['login_url'], settings.LOGIN_URL)

        # check not integer page
        request = self.factory.get('/?page=string')
        request.user = self.user_1
        data = render_comments(self.post_1, request, comments_per_page=2)
        self.assertFalse(data['comments'].has_previous())

        # check empty page
        request = self.factory.get('/?page=10')
        request.user = self.user_1
        data = render_comments(self.post_1, request, comments_per_page=2)
        self.assertTrue(data['comments'].has_previous())

    def test_static_functions(self):
        self.assertIsNone(include_static())
        self.assertIsNone(include_bootstrap())
        self.assertIsNone(include_static_jquery())

    def test_render_field(self):
        form = CommentForm()
        for field in form.visible_fields():
            self.assertIsNone(field.field.widget.attrs.get('placeholder'))
            field = render_field(field, placeholder='placeholder')
            self.assertEqual(field.field.widget.attrs.get('placeholder'), 'placeholder')

    def test_render_content(self):
        comment = self.parent_comment_1
        comment.content = "Any long text just for testing render content function"
        comment.save()
        content_words = comment.content.split(' ')
        self.assertEqual(len(content_words), 9)
        # truncate number is bigger than content words
        result = render_content(comment.content, 10)
        self.assertEqual(result['text_1'], comment.content)
        self.assertIsNone(result['text_2'])
        # truncate number is smaller than content words
        result = render_content(comment.content, 5)
        self.assertEqual(result['text_1'], ' '.join(content_words[:5]))
        self.assertEqual(result['text_2'], ' '.join(content_words[5:]))


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
