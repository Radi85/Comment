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


class GetModelObjectTest(BaseCommentUtilsTest):
    def test_success(self):
        data = {
            'app_name': 'post',
            'model_name': 'Post',
            'model_id': self.post_1.id
        }
        model_object = get_model_obj(**data)
        self.assertIsInstance(model_object, self.post_1.__class__)


class GetGratavarImgTest(BaseCommentUtilsTest):
    @patch.object(settings, 'COMMENT_USE_GRAVATAR', True)
    def test_without_email(self):
        self.assertEqual(get_gravatar_img(''), settings.COMMENT_DEFAULT_PROFILE_PIC_LOC)

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', True)
    def test_with_email(self):
        self.assertTrue(get_gravatar_img('test').startswith('https://www.gravatar.com/avatar/'))

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
    def test_disabling(self):
        self.assertEqual(get_gravatar_img(''), settings.COMMENT_DEFAULT_PROFILE_PIC_LOC)


class GetProfileInstanceTest(BaseCommentUtilsTest):
    @patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong')
    def test_wrong_content_type(self):
        self.assertIsNone(get_profile_instance(self.user_1))

    @patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile')
    def test_correct_content_type(self):
        self.assertIsNotNone(get_profile_instance(self.user_1))

    @patch.object(settings, 'PROFILE_MODEL_NAME', None)
    def test_profile_model_is_not_associated_with_user(self):
        self.assertIsNone(get_profile_instance(self.user_1))


@patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
@patch.object(settings, 'PROFILE_APP_NAME', 'user_profile')
class HasValidProfileTest(BaseCommentUtilsTest):
    def test_success(self):
        self.assertIs(has_valid_profile(), True)

    def test_model_provided_without_image(self):
        with patch('comment.utils.hasattr', return_value=False):
            self.assertIs(has_valid_profile(), False)

    @patch.object(settings, 'PROFILE_MODEL_NAME', '')
    def test_missing_setting_attribute(self):
        self.assertIs(has_valid_profile(), False)

    @patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong_value')
    def test_wrong_setting_attribute(self):
        self.assertIs(has_valid_profile(), False)

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', True)
    def test_gravatar_enabled(self):
        self.assertIs(has_valid_profile(), True)


class IsCommentModeratorTest(BaseCommentUtilsTest):
    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', False)
    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', False)
    def test_flagging_and_blocking_disabled(self):
        self.assertIs(is_comment_moderator(self.moderator), False)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', False)
    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_one_moderation_system_enabled(self):
        self.assertIs(is_comment_moderator(self.moderator), True)


class IsCommentAdminTest(BaseCommentUtilsTest):
    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', False)
    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', False)
    def test_flagging_and_blocking_disabled(self):
        self.assertIs(is_comment_admin(self.admin), False)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', False)
    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_one_moderation_system_enabled(self):
        self.assertIs(is_comment_admin(self.admin), True)


class GetUserForRequestTest(BaseCommentUtilsTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.request = cls.factory.get('/')

    def test_unauthenticated_user(self):
        self.request.user = AnonymousUser()
        self.assertIsNone(get_user_for_request(self.request))

    def test_authenticated_user(self):
        self.request.user = self.user_1
        self.assertEqual(get_user_for_request(self.request), self.user_1)


class GetWrappedWordsNumberTest(BaseCommentUtilsTest):
    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', None)
    def test_using_None(self):
        self.assertEqual(get_wrapped_words_number(), 0)

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', 'test')
    def test_using_non_integeral_value(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            get_wrapped_words_number()
        self.assertEqual(str(e.exception), ErrorMessage.WRAP_CONTENT_WORDS_NOT_INT)
        self.assertTextTranslated(ErrorMessage.WRAP_CONTENT_WORDS_NOT_INT)

    @patch.object(settings, 'COMMENT_WRAP_CONTENT_WORDS', 20)
    def test_using_integer_value(self):
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


class TestIdGenerator(BaseCommentUtilsTest):
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
