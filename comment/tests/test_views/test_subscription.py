from django.urls import reverse

from comment.tests.base import BaseCommentMixinTest
from comment.views import BaseToggleFollowView
from comment.messages import FollowError, EmailError
from comment.models import Follower


class BaseToggleFollowViewTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.view = BaseToggleFollowView()
        self.toggle_follow_url = self.get_url(
            reverse('comment:toggle-subscription'), app_name='comment', model_name='comment', model_id=self.comment.id
        )

    def test_assertion_error_on_missing_request_class(self):
        self.assertRaises(AssertionError, self.view.get_response_class)

    def test_success_on_providing_request_class(self):
        self.view.response_class = 'test'

        self.assertEqual(self.view.get_response_class(), self.view.response_class)

    def test_email_required_to_follow_object(self):
        self.client.force_login(self.user_without_email)
        response = self.client.post(self.toggle_follow_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['error']['email_required'], FollowError.EMAIL_REQUIRED.format(model_object=self.comment)
        )

    def test_invalid_email(self):
        self.client.force_login(self.user_1)
        data = {'email': 'invalid_email'}
        response = self.client.post(self.toggle_follow_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data=data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['invalid_email'], EmailError.EMAIL_INVALID)

    def test_toggle_follow_for_valid_email(self):
        self.client.force_login(self.user_without_email)
        self.assertEqual(self.user_without_email.email, '')
        data = {'email': 't@t.com'}
        self.assertFalse(Follower.objects.is_following(data['email'], self.comment))
        response = self.client.post(self.toggle_follow_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['following'])
        self.assertEqual(response.json()['data']['model_id'], self.comment.id)
        self.assertEqual(response.wsgi_request.user.email, data['email'])
        self.assertEqual(response.wsgi_request.user, self.user_without_email)

    def test_provide_email_for_user_has_already_email(self):
        self.client.force_login(self.user_2)
        self.assertEqual(self.user_2.email, 'test-2@acme.edu')
        data = {'email': 't@t.com'}
        self.assertFalse(Follower.objects.is_following(data['email'], self.comment))
        response = self.client.post(self.toggle_follow_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest', data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['following'])
        self.assertEqual(response.json()['data']['model_id'], self.comment.id)
        self.assertNotEqual(self.user_2, data['email'])
        self.assertEqual(response.wsgi_request.user, self.user_2)
