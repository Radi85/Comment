from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from comment.conf import settings
from comment.mixins import (
    AJAXRequiredMixin, BasePermission, ObjectLevelMixin, BaseCommentPermission, BaseCreatePermission
)
from comment.messages import ErrorMessage, FlagError, FollowError
from comment.tests.base import BaseCommentMixinTest, BaseCommentFlagTest


class AJAXMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.mixin = AJAXRequiredMixin()

    def test_non_ajax_request(self):
        response = self.mixin.dispatch(self.request)

        self.assert_permission_denied_response(response, reason=ErrorMessage.NON_AJAX_REQUEST)


class BasePermissionTest(BaseCommentMixinTest):
    def test_has_permission(self):
        self.assertTrue(BasePermission().has_permission(self.request))

    @patch('comment.mixins.BasePermission.has_permission', return_value=False)
    def test_dispatch_with_no_permission(self, _):
        response = BasePermission().dispatch(self.request)

        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)


class BaseCommentPermissionTest(BaseCommentMixinTest):
    def test_has_permission_for_anonymous_user(self):
        self.request.user = AnonymousUser()
        permission = BaseCommentPermission()

        self.assertFalse(permission.has_permission(self.request))
        self.assertEqual(permission.reason, ErrorMessage.LOGIN_REQUIRED)


class BaseCreatePermissionTest(BaseCommentMixinTest):
    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_has_permission_for_anonymous_user_when_settings_not_enabled(self):
        self.request.user = AnonymousUser()
        permission = BaseCreatePermission()

        self.assertFalse(permission.has_permission(self.request))
        self.assertEqual(permission.reason, ErrorMessage.LOGIN_REQUIRED)


class CanCreateMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.url = reverse('comment:create')
        self.client.force_login(self.user_1)

    def test_logged_in_user_permission(self):
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_logged_out_user_permission(self, ):
        self.client.logout()

        response = self.client.post(self.url, data=self.data)

        self.assert_permission_denied_response(response, reason=ErrorMessage.LOGIN_REQUIRED)

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_permission_when_anonymous_comment_allowed(self):
        self.client.logout()
        self.data['email'] = 'test@test.come'

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)


class ObjectLevelMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.object_mixin = ObjectLevelMixin()

    def test_get_object_without_overriding(self):

        self.assertRaises(ImproperlyConfigured, self.object_mixin.get_object)

    def test_has_object_permission(self):
        self.assertTrue(self.object_mixin.has_object_permission(self.request, self.comment))

    @patch('comment.mixins.ObjectLevelMixin.has_object_permission', return_value=False)
    @patch('comment.mixins.ObjectLevelMixin.get_object')
    def test_dispatch_with_no_object_permission(self, *args):
        response = self.object_mixin.dispatch(self.request)

        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)


class CanEditMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:edit', kwargs={'pk': self.comment.id})

    def test_comment_owner_can_edit(self):
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)

    def test_edit_comment_by_non_owner(self):
        self.assertNotEqual(self.comment.user.id, self.user_2.id)
        self.client.force_login(self.user_2)

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

    def test_edit_comment_by_anonymous(self):
        self.client.logout()

        response = self.client.post(self.url, data=self.data)

        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)


class CanDeleteMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:delete', kwargs={'pk': self.comment.id})

    def test_delete_comment_by_owner(self):
        self.assertEqual(self.comment.user.id, self.user_1.id)

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)

    def test_delete_comment_by_non_owner(self):
        self.assertNotEqual(self.comment.user.id, self.user_2.id)
        self.client.force_login(self.user_2)

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

    def test_delete_comment_by_admin(self):
        self.assertNotEqual(self.comment.user.id, self.admin.id)
        self.client.force_login(self.admin)

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)

    def test_delete_comment_by_moderator(self):
        """moderator cannot delete comment unless it's flagged"""
        self.assertNotEqual(self.comment.user.id, self.moderator.id)
        self.client.force_login(self.moderator)

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_delete_flagged_comment_by_moderator(self):
        """moderator cannot delete comment unless it's flagged"""
        self.assertNotEqual(self.comment.user.id, self.moderator.id)
        self.client.force_login(self.moderator)
        self.create_flag_instance(self.moderator, self.comment)
        self.create_flag_instance(self.admin, self.comment)
        self.assertEqual(self.flags, 2)

        self.assertTrue(self.comment.is_flagged)

        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 200)


class BaseFlagMixinTest(BaseCommentFlagTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:flag', kwargs={'pk': self.comment_2.id})

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_flag_not_enabled_permission(self):
        """permission denied when flagging not enabled"""
        self.client.force_login(self.user_2)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=FlagError.SYSTEM_NOT_ENABLED)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 2)
    def test_flag_enabled_permission(self):
        self.client.force_login(self.user_2)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)


class CanSetFlagMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:flag', kwargs={'pk': self.comment.id})

    def test_user_cannot_flag_their_own_comment(self):
        self.assertEqual(self.comment.user.id, self.user_1.id)
        self.client.force_login(self.user_1)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)


class CanEditFlagStateMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user_1)
        self.url = reverse('comment:flag-change-state', kwargs={'pk': self.comment.id})
        self.data = {'state': 3}

    def test_change_state_of_unflagged_comment(self):
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_moderator_can_change_flag_state(self):
        self.create_flag_instance(self.admin, self.comment)
        self.create_flag_instance(self.moderator, self.comment)
        self.comment.flag.refresh_from_db()
        self.assertEqual(self.flags, 2)
        self.assertTrue(self.comment.is_flagged)

        # normal user cannot change flag state
        self.client.force_login(self.user_2)
        response = self.client.post(self.url, data=self.data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

        self.client.force_login(self.moderator)
        response = self.client.post(self.url, data=self.data)

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

        response = self.client.post(self.toggle_follow_url)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=FollowError.SYSTEM_NOT_ENABLED)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_user_can_subscribe(self):
        self.client.force_login(self.user_1)
        self.assertTrue(settings.COMMENT_ALLOW_SUBSCRIPTION)

        response = self.client.post(self.toggle_follow_url)

        self.assertEqual(response.status_code, 200)


class CanBlockUsersMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.toggle_blocking_url = self.get_url(reverse('comment:toggle-blocking'))

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', False)
    def test_admin_cannot_block_users_when_system_disabled(self):
        self.client.force_login(self.admin)
        self.assertFalse(settings.COMMENT_ALLOW_BLOCKING_USERS)
        data = {'comment_id': self.comment.id}

        response = self.client.post(self.toggle_blocking_url, data=data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_non_moderate_cannot_block_users_when_system_enabled(self):
        self.client.force_login(self.user_1)
        self.assertTrue(settings.COMMENT_ALLOW_BLOCKING_USERS)
        data = {'comment_id': self.comment.id}

        response = self.client.post(self.toggle_blocking_url, data=data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_admin_can_block_users_when_system_enabled(self):
        self.client.force_login(self.admin)
        self.assertTrue(settings.COMMENT_ALLOW_BLOCKING_USERS)
        data = {'comment_id': self.comment.id}

        response = self.client.post(self.toggle_blocking_url, data=data)

        self.assertEqual(response.status_code, 200)

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    @patch.object(settings, 'COMMENT_ALLOW_MODERATOR_TO_BLOCK', False)
    def test_moderator_cannot_block_user_when_moderation_system_disabled(self):
        self.client.force_login(self.moderator)
        self.assertTrue(settings.COMMENT_ALLOW_BLOCKING_USERS)
        data = {'comment_id': self.comment.id}

        response = self.client.post(self.toggle_blocking_url, data=data)

        self.assertEqual(response.status_code, 403)
        self.assert_permission_denied_response(response, reason=ErrorMessage.NOT_AUTHORIZED)

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    @patch.object(settings, 'COMMENT_ALLOW_MODERATOR_TO_BLOCK', True)
    def test_moderator_cannot_block_user_when_moderation_system_enabled(self):
        self.client.force_login(self.moderator)
        self.assertTrue(settings.COMMENT_ALLOW_BLOCKING_USERS)
        data = {'comment_id': self.comment.id}

        response = self.client.post(self.toggle_blocking_url, data=data)

        self.assertEqual(response.status_code, 200)
