from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Page

from comment.conf import settings

from comment.tests.base import BaseCommentUtilsTest
from comment.context import DABContext
from comment.messages import ErrorMessage


class DABContextTest(BaseCommentUtilsTest):
    def setUp(self):
        super().setUp()
        self.data = {
            'model_object': self.post_1,
            'model_name': 'post',
            'model_id': self.post_1.id,
            'app_name': 'post',
            'user': self.post_1.author,
            'page': 10,
        }
        self.request = self.factory.post('/', data=self.data)
        self.request.user = self.post_1.author

    def test_initialized_object_is_dict(self):
        self.assertIsInstance(DABContext(self.request), dict)

    def test_model_object_exist_even_if_not_provided(self):
        self.assertEqual(DABContext(self.request).model_object, self.post_1)

    @patch.object(settings, 'LOGIN_URL', None)
    def test_get_login_url_fails_when_missing_in_settings(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            DABContext(self.request)
        self.assertEqual(e.exception.args[0], ErrorMessage.LOGIN_URL_MISSING)

    @patch.object(settings, 'LOGIN_URL', 'profile/login/')
    def test_get_login_url_prepend_slash(self):
        self.assertFalse(settings.LOGIN_URL.startswith('/'))
        self.assertTrue(DABContext(self.request).get('login_url').startswith('/'))

    @patch.object(settings, 'LOGIN_URL', '/profile/login/')
    def test_get_login_url_success(self):
        self.assertTrue(DABContext(self.request).get('login_url'), '/profile/login/')

    def test_is_oauth_true(self):
        self.data['oauth'] = True
        request = self.factory.post('/', data=self.data)
        request.user = self.post_1.author
        context = DABContext(request)
        self.assertTrue(context['oauth'])

    def test_is_oauth_false(self):
        self.data['oauth'] = False
        request = self.factory.post('/', data=self.data)
        request.user = self.post_1.author
        context = DABContext(request)
        self.assertFalse(context['oauth'])

    @patch.object(settings, 'COMMENT_PER_PAGE', 0)
    def test_get_comments_without_pagination(self):
        context = DABContext(self.request)
        self.assertEqual(context['comments'].count(), self.increment)
        self.assertNotIsInstance(context['comments'], Page)

    @patch.object(settings, 'COMMENT_PER_PAGE', 2)
    def test_get_comments_with_pagination(self):
        context = DABContext(self.request)
        self.assertEqual(context['comments'].paginator.per_page, 2)
        self.assertIsInstance(context['comments'], Page)

    def test_context_object_is_callable(self):
        context = DABContext(self.request)
        self.assertTrue(callable(context))

    def test_calling_text_object_return_default_values(self):
        context = DABContext(self.request, extra_1='test-1')
        self.assertEqual(len(context), len(context.__call__()) + 1)
        self.assertEqual(len(context()), len(context.__call__()))
