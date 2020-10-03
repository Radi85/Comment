from unittest import TestCase
from unittest.mock import patch

from django.utils import timezone
from django.core import signing
from django.contrib.auth.models import AnonymousUser

from comment.conf import settings
from comment.utils import (
    get_model_obj, has_valid_profile, get_comment_context_data, id_generator, get_comment_from_key,
    get_user_for_request, CommentFailReason,
    get_gravatar_img, get_profile_instance, is_comment_moderator, is_comment_admin, get_username_for_comment)
from comment.tests.base import BaseCommentUtilsTest, Comment, RequestFactory


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

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', True)
    def test_get_gravatar_img(self):
        # email is not provided
        self.assertEqual(get_gravatar_img(''), '/static/img/default.png')

        # email is provided
        self.assertTrue(get_gravatar_img('test').startswith('https://www.gravatar.com/avatar/'))

        # gravatar is disabled
        patch.object(settings, 'COMMENT_USE_GRAVATAR', True).start()
        self.assertEqual(get_gravatar_img(''), '/static/img/default.png')

    def test_get_profile_instance(self):
        # wrong content type
        patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong').start()
        self.assertIsNone(get_profile_instance(self.user_1))

        # correct data
        patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile').start()
        self.assertIsNotNone(get_profile_instance(self.user_1))

        # profile model has no user related model
        patch.object(settings, 'PROFILE_MODEL_NAME', None).start()
        self.assertIsNone(get_profile_instance(self.user_1))

    @patch.object(settings, 'COMMENT_USE_GRAVATAR', False)
    def test_has_valid_profile(self):
        patch.object(settings, 'PROFILE_APP_NAME', 'user_profile').start()
        patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile').start()
        self.assertTrue(has_valid_profile())

        # one of settings attribute is missing
        patch.object(settings, 'PROFILE_MODEL_NAME', '').start()
        self.assertFalse(has_valid_profile())

        # settings attr provided with wrong value
        patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong_value').start()
        self.assertFalse(has_valid_profile())

        # settings attr provided, profile model has no image
        patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile').start()
        mocked_hasattr = patch('comment.utils.hasattr').start()
        mocked_hasattr.return_value = False
        self.assertFalse(has_valid_profile())

        patch.object(settings, 'COMMENT_USE_GRAVATAR', True).start()
        self.assertTrue(has_valid_profile())

    def test_get_comment_context_data(self):
        comment_per_page = 'COMMENT_PER_PAGE'
        login_url = 'LOGIN_URL'
        current_login_url = getattr(settings, login_url, '/profile/login/')
        comment_allow_anonymous = 'COMMENT_ALLOW_ANONYMOUS'
        comment_allow_translation = 'COMMENT_ALLOW_TRANSLATION'
        oauth = 'oauth'

        patch.object(settings, login_url, current_login_url).start()
        patch.object(settings, comment_allow_anonymous, False).start()
        patch.object(settings, comment_per_page, 0).start()

        data = {
            'model_object': self.post_1,
            'model_name': 'post',
            'model_id': self.post_1.id,
            'app_name': 'post',
            'user': self.post_1.author,
            'page': 10,
            oauth: 'True'
        }
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        if current_login_url.startswith('/'):
            patch.object(settings, login_url, current_login_url[1:]).start()
        comment_context_data = get_comment_context_data(request)

        self.assertEqual(comment_context_data['comments'].count(), self.increment)
        # test inserting '/' to the beginning of login url
        self.assertEqual(comment_context_data['login_url'], '/' + settings.LOGIN_URL)
        self.assertEqual(comment_context_data['is_anonymous_allowed'], settings.COMMENT_ALLOW_ANONYMOUS)
        self.assertEqual(comment_context_data['is_translation_allowed'], settings.COMMENT_ALLOW_TRANSLATION)
        self.assertEqual(comment_context_data['oauth'], True)

        patch.object(settings, login_url, current_login_url).start()
        patch.object(settings, comment_allow_anonymous, True).start()
        patch.object(settings, comment_allow_translation, False).start()
        patch.object(settings, comment_per_page, 2).start()
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        comment_context_data = get_comment_context_data(request)

        self.assertEqual(comment_context_data['comments'].paginator.per_page, 2)
        self.assertTrue(comment_context_data['comments'].has_previous())
        self.assertEqual(comment_context_data['login_url'], settings.LOGIN_URL)
        self.assertEqual(comment_context_data['is_anonymous_allowed'], settings.COMMENT_ALLOW_ANONYMOUS)
        self.assertEqual(comment_context_data['is_translation_allowed'], settings.COMMENT_ALLOW_TRANSLATION)

        data.update({'page': 'not integer', oauth: 'False'})
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        comment_context_data = get_comment_context_data(request)

        self.assertEqual(comment_context_data['comments'].paginator.per_page, 2)
        self.assertTrue(comment_context_data['comments'].has_next())
        self.assertEqual(comment_context_data[oauth], False)

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

    def test_get_username_for_comment(self):
        comment = self.create_comment(self.content_object_1, user=self.user_1)
        anonymous_comment = self.create_anonymous_comment()

        self.assertEqual(get_username_for_comment(comment), comment.user.username)
        patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', False).start()
        self.assertEqual(get_username_for_comment(anonymous_comment), settings.COMMENT_ANONYMOUS_USERNAME)

        patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', True).start()
        self.assertEqual(get_username_for_comment(anonymous_comment), anonymous_comment.email.split('@')[0])


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
