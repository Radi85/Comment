from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.core import signing
from django.contrib.auth.models import AnonymousUser

from comment.conf import settings
from comment.utils import (
    get_model_obj, has_valid_profile, id_generator, get_comment_from_key, get_user_for_request, CommentFailReason,
    get_gravatar_img, get_profile_instance, is_comment_moderator, is_comment_admin, get_wrapped_words_number
)
from comment.tests.base import BaseCommentUtilsTest, Comment, RequestFactory
from comment.messages import ErrorMessage


class CommentUtilsTest(BaseCommentUtilsTest):
    def test_get_model_object(self):
        data = {
            'app_name': 'post',
            'model_name': 'Post',
            'model_id': self.post_1.id
        }
        model_object = get_model_obj(**data)
        self.assertIsNotNone(model_object)
        self.assertIsInstance(model_object, self.post_1.__class__)

    def test_get_gravatar_img(self):
        with patch.object(settings, 'COMMENT_USE_GRAVATAR', True):
            # email is not provided
            self.assertEqual(get_gravatar_img(''), '/static/img/default.png')

            # email is provided
            self.assertTrue(get_gravatar_img('test').startswith('https://www.gravatar.com/avatar/'))

        # gravatar is disabled
        with patch.object(settings, 'COMMENT_USE_GRAVATAR', False):
            self.assertEqual(get_gravatar_img(''), '/static/img/default.png')

    def test_get_profile_instance(self):
        # wrong content type
        with patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong'):
            self.assertIsNone(get_profile_instance(self.user_1))

        # correct data
        with patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile'):
            self.assertIsNotNone(get_profile_instance(self.user_1))

        # profile model has no user related model
        with patch.object(settings, 'PROFILE_MODEL_NAME', None):
            self.assertIsNone(get_profile_instance(self.user_1))

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
    def test_has_valid_profile(self):
        with patch.object(settings, 'PROFILE_APP_NAME', 'user_profile'):
            with patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile'):
                self.assertIs(has_valid_profile(), True)

            # settings attr provided, profile model has no image
            with patch('comment.utils.hasattr', return_value=False):
                self.assertIs(has_valid_profile(), False)

            # one of settings attribute is missing
            with patch.object(settings, 'PROFILE_MODEL_NAME', ''):
                self.assertIs(has_valid_profile(), False)

            # settings attr provided with wrong value
            with patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong_value'):
                self.assertIs(has_valid_profile(), False)

            with patch.object(settings, 'COMMENT_USE_GRAVATAR', True):
                self.assertIs(has_valid_profile(), True)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', False)
    def test_is_comment_moderator_no_moderation(self):
        self.assertFalse(is_comment_moderator(self.moderator))

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', False)
    def test_is_comment_admin_no_moderation(self):
        self.assertFalse(is_comment_admin(self.admin))

    def test_user_for_request(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        # test unauthenticated user
        self.assertIsNone(get_user_for_request(request))
        # test authenticated user
        request.user = self.user_1
        self.assertEqual(get_user_for_request(request), self.user_1)

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', None)
    def test_get_wrapped_words_number_return_0_for_None(self):
        self.assertEqual(get_wrapped_words_number(), 0)

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', 'test')
    def test_get_wrapped_words_number_fails_on_non_int_value(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            get_wrapped_words_number()
        self.assertEqual(str(e.exception), ErrorMessage.WRAP_CONTENT_WORDS_NOT_INT)
        self.assertTextTranslated(ErrorMessage.WRAP_CONTENT_WORDS_NOT_INT)

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', 20)
    def test_get_wrapped_words_number_return_specified_setting_value(self):
        self.assertEqual(get_wrapped_words_number(), 20)


class BaseAnonymousCommentTest(BaseCommentUtilsTest):
    def setUp(self):
        super().setUp()
        self.time_posted = timezone.now()
        _email = 'test-1@acme.edu'
        _content = 'posting anonymous comment'
        _parent = None
        _factory = RequestFactory()
        self.comment_obj = Comment(
            content_object=self.post_1,
            content=_content,
            user=None,
            parent=_parent,
            email=_email,
            posted=self.time_posted
        )

        self.key = signing.dumps(self.comment_obj.to_dict(), compress=True)
        self.request = _factory.get('/')


class TestGetCommentFromKey(BaseAnonymousCommentTest):
    def test_bad_signature(self):
        key = self.key + 'invalid'
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_key_error(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment_dict.pop('model_name')
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_attribute_error(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment_dict['model_name'] = 1
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_value_error(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment_dict['user'] = 1
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_comment_exists(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment = self.create_anonymous_comment(posted=timezone.now(), email='a@a.com')
        comment_dict.update({
            'posted': str(comment.posted),
            'email': comment.email
        })
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.EXISTS)
        self.assertIsNone(response.obj)

    def test_success(self):
        response = get_comment_from_key(self.key)

        self.assertEqual(response.is_valid, True)
        self.assertEqual(response.why_invalid, None)
        self.assertIsInstance(response.obj, Comment)


class UtilsTest(TestCase):
    """Test general purpose utilities that aren't necessarily related to a comment"""

    def setUp(self):
        self.len_id = 6

    def test_id_generator_length(self):
        self.assertEqual(self.len_id, len(id_generator()))

    def test_id_generator_generates_different_ids(self):
        self.assertNotEqual(id_generator(), id_generator())

    def test_id_generator_prefix(self):
        prefix = 'comment'
        output = id_generator(prefix=prefix)
        self.assertEqual(True, output.startswith(prefix))
        self.assertEqual(self.len_id + len(prefix), len(output))

    def test_id_generator_suffix(self):
        suffix = 'comment'
        output = id_generator(suffix=suffix)
        self.assertEqual(True, output.endswith(suffix))
        self.assertEqual(self.len_id + len(suffix), len(output))

    def test_id_generator_chars(self):
        import string   # flake8:no qa
        chars = string.ascii_uppercase
        output = id_generator(chars=chars)
        self.assertEqual(output, output.upper())

    def test_id_generator_len(self):
        len_id = 8
        self.assertEqual(len_id, len(id_generator(len_id=len_id)))
