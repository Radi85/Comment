from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from rest_framework import status

from comment.conf import settings
from comment.mixins import AJAXRequiredMixin, BasePermission, ObjectLevelMixin
from comment.messages import ErrorMessage
from comment.tests.base import BaseCommentMixinTest, BaseCommentFlagTest


class AJAXMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.mixin = AJAXRequiredMixin()

    def test_non_ajax_request(self):
        request = self.factory.get('/')
        response = self.mixin.dispatch(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content.decode('utf-8'), ErrorMessage.NON_AJAX_REQUEST)


class BasePermissionTest(BaseCommentMixinTest):
    def test_has_permission(self):
        request = self.factory.get('/')
        self.assertTrue(BasePermission().has_permission(request))

    def test_has_object_permission(self):
        request = self.factory.get('/')
        self.assertTrue(BasePermission().has_object_permission(request, 'object'))


class CanCreateMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('comment:create')
        self.client.force_login(self.user_1)

    def test_logged_in_user_permission(self):
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_logged_out_user_permission(self, ):
        self.client.logout()
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 302)
        # user will be redirected to login
        self.assertEqual(response.url, settings.LOGIN_URL + '?next=/comment/create/')

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_permission_when_anonymous_comment_allowed(self):
        self.client.logout()
        self.data['email'] = 'test@test.come'
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)


class ObjectLevelMixinTest(BaseCommentMixinTest):
    def test_get_object_without_overriding(self):
        object_mixin = ObjectLevelMixin()
        self.assertRaises(ImproperlyConfigured, object_mixin.get_object)


class CanEditMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:edit', kwargs={'pk': self.comment.id})

    def test_comment_owner_can_edit(self):
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_edit_comment_by_non_owner(self):
        self.assertNotEqual(self.comment.user.id, self.user_2.id)
        self.client.force_login(self.user_2)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    def test_edit_comment_by_anonymous(self):
        """anonymous will be redirected to login page"""
        self.client.logout()
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, settings.LOGIN_URL + f'?next=/comment/edit/{self.comment.id}/')


class CanDeleteMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:delete', kwargs={'pk': self.comment.id})

    def test_delete_comment_by_owner(self):
        self.assertEqual(self.comment.user.id, self.user_1.id)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_delete_comment_by_non_owner(self):
        self.assertNotEqual(self.comment.user.id, self.user_2.id)
        self.client.force_login(self.user_2)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    def test_delete_comment_by_admin(self):
        self.assertNotEqual(self.comment.user.id, self.admin.id)
        self.client.force_login(self.admin)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_delete_comment_by_moderator(self):
        """moderator cannot delete comment unless it's flagged"""
        self.assertNotEqual(self.comment.user.id, self.moderator.id)
        self.client.force_login(self.moderator)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    def test_delete_flagged_comment_by_moderator(self):
        """moderator cannot delete comment unless it's flagged"""
        self.assertNotEqual(self.comment.user.id, self.moderator.id)
        self.client.force_login(self.moderator)
        self.create_flag_instance(self.user_2, self.comment)
        self.create_flag_instance(self.admin, self.comment)
        self.create_flag_instance(self.moderator, self.comment)
        self.assertEqual(self.flags, 3)
        self.assertTrue(self.comment.is_flagged)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)


class BaseFlagMixinTest(BaseCommentFlagTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:flag', kwargs={'pk': self.comment_2.id})

    @patch('comment.mixins.settings', COMMENT_FLAGS_ALLOWED=0)
    def test_flag_not_enabled_permission(self, _):
        """permission denied when flagging not enabled"""
        self.client.force_login(self.user_2)
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    @patch('comment.mixins.settings', COMMENT_FLAGS_ALLOWED=2)
    def test_flag_enabled_permission(self, _):
        self.client.force_login(self.user_2)
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)


class CanSetFlagMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:flag', kwargs={'pk': self.comment.id})

    def test_user_cannot_flag_their_own_comment(self):
        self.assertEqual(self.comment.user.id, self.user_1.id)
        self.client.force_login(self.user_1)
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)


class CanEditFlagStateMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:flag-change-state', kwargs={'pk': self.comment.id})
        self.data = {'state': 3}

    def test_change_state_of_unflagged_comment(self):
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)

    def test_moderator_can_change_flag_state(self):
        self.create_flag_instance(self.user_2, self.comment)
        self.create_flag_instance(self.admin, self.comment)
        self.create_flag_instance(self.moderator, self.comment)
        self.comment.flag.refresh_from_db()
        self.assertEqual(self.flags, 3)
        self.assertTrue(self.comment.is_flagged)
        # normal user cannot change flag state
        self.client.force_login(self.user_2)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.moderator)
        response = self.client.post(self.url, data=self.data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)


class CanSubscribeMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.toggle_follow_url = self.get_url(
            reverse('comment:toggle-subscription'), app_name='comment', model_name='comment', model_id=self.comment.id
        )

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_user_cannot_subscribe(self):
        self.client.force_login(self.user_1)
        self.assertFalse(settings.COMMENT_ALLOW_SUBSCRIPTION)
        response = self.client.post(self.toggle_follow_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_user_can_subscribe(self):
        self.client.force_login(self.user_1)
        self.assertTrue(settings.COMMENT_ALLOW_SUBSCRIPTION)
        response = self.client.post(self.toggle_follow_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
