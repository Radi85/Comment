from django.urls import reverse

from comment.tests.base import BaseCommentMixinTest
from comment.views import BaseToggleBlockingView
from comment.messages import BlockUserError
from comment.models import BlockedUser


class BaseToggleBlockingViewTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.view = BaseToggleBlockingView()
        self.client.force_login(self.admin)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_for_blocking = cls.create_comment(cls.post_1, user=cls.user_1)
        cls.anonymous_comment_for_blocking = cls.create_anonymous_comment(cls.post_1, email='test@test.com')
        cls.toggle_blocking_url = cls.get_url(reverse('comment:toggle-blocking'))

    def test_assertion_error_on_missing_request_class(self):
        self.assertRaises(AssertionError, self.view.get_response_class)

    def test_success_on_providing_request_class(self):
        self.view.response_class = 'test'

        self.assertEqual(self.view.get_response_class(), self.view.response_class)

    def test_block_comment_user_by_passing_non_int_comment_id(self):
        data = {'comment_id': 'non int'}
        response = self.client.post(self.toggle_blocking_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['detail'], BlockUserError.INVALID)

    def test_block_comment_user_with_missing_comment_id(self):
        response = self.client.post(self.toggle_blocking_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['detail'], BlockUserError.INVALID)

    def test_block_comment_user_for_not_existing_comment(self):
        data = {'comment_id': 1000}
        response = self.client.post(self.toggle_blocking_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['detail'], BlockUserError.INVALID)

    def test_block_comment_user(self):
        self.assertFalse(BlockedUser.objects.is_user_blocked(user_id=self.comment_for_blocking.user.id))

        data = {'comment_id': self.comment_for_blocking.id}
        response = self.client.post(self.toggle_blocking_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['blocked_user'], self.comment_for_blocking.get_username())
        self.assertTrue(response.json()['data']['blocked'])
        self.assertEqual(response.json()['data']['urlhash'], self.comment_for_blocking.urlhash)

        self.assertTrue(BlockedUser.objects.is_user_blocked(user_id=self.comment_for_blocking.user.id))

    def test_block_anonymous_comment_email(self):
        self.assertFalse(BlockedUser.objects.is_user_blocked(email=self.anonymous_comment_for_blocking.email))

        data = {'comment_id': self.anonymous_comment_for_blocking.id}
        response = self.client.post(self.toggle_blocking_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['blocked_user'], self.anonymous_comment_for_blocking.get_username())
        self.assertTrue(response.json()['data']['blocked'])
        self.assertEqual(response.json()['data']['urlhash'], self.anonymous_comment_for_blocking.urlhash)

        self.assertTrue(BlockedUser.objects.is_user_blocked(email=self.anonymous_comment_for_blocking.email))

    def test_toggling_blocking(self):
        self.assertFalse(BlockedUser.objects.is_user_blocked(user_id=self.comment_for_blocking.user.id))

        data = {'comment_id': self.comment_for_blocking.id}

        # first call
        response = self.client.post(self.toggle_blocking_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['blocked'])

        self.assertTrue(BlockedUser.objects.is_user_blocked(user_id=self.comment_for_blocking.user.id))

        # second call
        data['reason'] = 'promise to be good boy :)'
        response = self.client.post(self.toggle_blocking_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['data']['blocked'])

        self.assertFalse(BlockedUser.objects.is_user_blocked(user_id=self.comment_for_blocking.user.id))
