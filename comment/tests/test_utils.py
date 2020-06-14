from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory

from comment.utils import get_model_obj, has_valid_profile, get_comment_context_data
from comment.tests.base import BaseCommentTest


class UtilsTest(BaseCommentTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.comment_1 = self.create_comment(self.content_object_1)
        self.comment_2 = self.create_comment(self.content_object_1)
        self.comment_3 = self.create_comment(self.content_object_1)

    def test_get_model_object(self):
        data = {
            'app_name': 'post',
            'model_name': 'Post',
            'model_id': self.post_1.id
        }
        model_object = get_model_obj(**data)
        self.assertIsNotNone(model_object)
        self.assertIsInstance(model_object, self.post_1.__class__)

    def test_has_valid_profile(self):
        setattr(settings, 'PROFILE_APP_NAME', 'user_profile')
        setattr(settings, 'PROFILE_MODEL_NAME', 'userprofile')
        has_profile = has_valid_profile()
        self.assertTrue(has_profile)

        # one of settings attribute is missing
        setattr(settings, 'PROFILE_MODEL_NAME', '')
        has_profile = has_valid_profile()
        self.assertFalse(has_profile)

        # settings attr provided with wrong value
        setattr(settings, 'PROFILE_MODEL_NAME', 'wrong_value')
        has_profile = has_valid_profile()
        self.assertFalse(has_profile)

        # settings attr provided, profile model has no image
        setattr(settings, 'PROFILE_MODEL_NAME', 'userprofile')
        mocked_hasattr = patch('comment.utils.hasattr').start()
        mocked_hasattr.return_value = False
        has_profile = has_valid_profile()
        self.assertFalse(has_profile)

    def test_get_comment_context_data(self):
        setattr(settings, 'LOGIN_URL', 'login')
        data = {
            'model_object': self.post_1,
            'model_name': 'post',
            'model_id': self.post_1.id,
            'app_name': 'post',
            'user': self.post_1.author,
            'comments_per_page': '',
            'page': 10
        }
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        comment_context_data = get_comment_context_data(request)
        self.assertEqual(comment_context_data['comments'].count(), 3)
        self.assertEqual(comment_context_data['login_url'], '/'+settings.LOGIN_URL)

        data['comments_per_page'] = 2
        setattr(settings, 'LOGIN_URL', '/login')
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        comment_context_data = get_comment_context_data(request)
        self.assertEqual(comment_context_data['comments'].paginator.per_page, 2)
        self.assertTrue(comment_context_data['comments'].has_previous())
        self.assertEqual(comment_context_data['login_url'], settings.LOGIN_URL)

        data['comments_per_page'] = 2
        data['page'] = 'not integer'
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        comment_context_data = get_comment_context_data(request)
        self.assertEqual(comment_context_data['comments'].paginator.per_page, 2)
        self.assertTrue(comment_context_data['comments'].has_next())
