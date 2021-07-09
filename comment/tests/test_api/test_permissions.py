from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from comment.tests.test_api.test_views import BaseAPITest
from comment.api.permissions import (
    IsOwnerOrReadOnly, FlagEnabledPermission, CanChangeFlaggedCommentState, SubscriptionEnabled,
    CanGetSubscribers, UserPermittedOrReadOnly, CanCreatePermission, CanBlockUsers
)
from comment.api.views import CommentList
from comment.managers import FlagInstanceManager
from comment.conf import settings


class BaseAPIPermissionsTest(BaseAPITest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.factory = RequestFactory()

    def setUp(self):
        super().setUp()
        self.view = CommentList()


class OwnerPermissionTest(BaseAPIPermissionsTest):
    def setUp(self):
        super().setUp()
        self.permission = IsOwnerOrReadOnly()

    def test_get_request(self):
        request = self.factory.get('/')

        self.assertTrue(self.permission.has_object_permission(request, self.view, self.comment_1))

    def test_put_method_from_different_user(self):
        request = self.factory.put('/')
        request.user = self.user_2
        self.assertEqual(self.comment_1.user, self.user_1)

        self.assertFalse(self.permission.has_object_permission(request, self.view, self.comment_1))

    def test_put_method_from_admin(self):
        request = self.factory.put('/')
        request.user = self.admin
        self.assertEqual(self.comment_1.user, self.user_1)

        self.assertFalse(self.permission.has_object_permission(request, self.view, self.comment_1))

    def test_put_method_from_same_user(self):
        request = self.factory.put('/')
        request.user = self.user_1
        self.assertEqual(self.comment_1.user, self.user_1)

        self.assertTrue(self.permission.has_object_permission(request, self.view, self.comment_1))


class FlagEnabledPermissionTest(BaseAPIPermissionsTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.request = cls.factory.get('/')

    def setUp(self):
        super().setUp()
        self.permission = FlagEnabledPermission()

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_flagging_disabled(self):
        self.assertIs(False, self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_flagging_enabled(self):
        self.assertIs(True, self.permission.has_permission(self.request, self.view))


class CanChangeFlaggedCommentStateTest(BaseAPIPermissionsTest):
    @classmethod
    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag_data = {
            'reason': FlagInstanceManager.reason_values[0],
            'info': '',
        }
        cls.create_flag_instance(cls.user_1, cls.comment_1, **cls.flag_data)
        cls.create_flag_instance(cls.user_2, cls.comment_1, **cls.flag_data)
        cls.comment_1.flag.refresh_from_db()
        cls.flagged_comment = cls.comment_1
        cls.unflagged_comment = cls.comment_2

    def setUp(self):
        super().setUp()
        self.permission = CanChangeFlaggedCommentState()
        self.request = self.factory.get('/')
        self.request.user = self.user_1

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', True)
    def test_normal_user(self):
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', True)
    def test_moderator(self):
        self.request.user = self.moderator

        self.assertTrue(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', False)
    def test_flagging_system_disabled(self):
        self.request.user = self.moderator

        self.assertFalse(self.permission.has_permission(self.request, self.view))

    def test_can_change_for_flagged_comment(self):
        self.assertIs(
            True,
            self.permission.has_object_permission(self.request, self.view, self.flagged_comment)
        )

    def test_cannot_change_for_unflagged_comment(self):
        self.assertIs(
            False,
            self.permission.has_object_permission(self.request, self.view, self.unflagged_comment)
        )


class CanGetSubscribersTest(BaseAPIPermissionsTest):
    def setUp(self):
        super().setUp()
        self.permission = CanGetSubscribers()
        self.request = self.factory.get('/')

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_normal_users_cannot_retrieve_subscribers(self):
        self.request.user = self.user_1

        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_only_moderators_can_retrieve_subscribers(self):
        self.request.user = self.moderator

        self.assertTrue(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_cannot_retrieve_subscribers_when_system_disabled(self):
        self.request.user = self.moderator

        self.assertFalse(self.permission.has_permission(self.request, self.view))


class SubscriptionEnabledTest(BaseAPIPermissionsTest):
    def setUp(self):
        super().setUp()
        self.request = self.factory.post('/')
        self.permission = SubscriptionEnabled()

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_when_subscription_disabled(self):
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_when_permission(self):
        self.assertTrue(self.permission.has_permission(self.request, self.view))


class UserPermittedOrReadOnlyTest(BaseAPIPermissionsTest):
    def setUp(self):
        super().setUp()
        self.permission = UserPermittedOrReadOnly()

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_user_has_permission_for_safe_method(self, *arg):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self.assertTrue(self.permission.has_permission(request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', False)
    def test_user_has_permission_when_blocking_system_not_enabled(self, *arg):
        request = self.factory.post('/')
        request.user = AnonymousUser()
        self.assertTrue(self.permission.has_permission(request, self.view))

    @patch('comment.managers.BlockedUserManager.is_user_blocked', return_value=True)
    def test_blocked_user_has_no_permission(self, *arg):
        request = self.factory.post('/')
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, self.view))


class CanCreatePermissionTest(BaseAPIPermissionsTest):
    def setUp(self):
        super().setUp()
        self.request = self.factory.get('/')
        self.permission = CanCreatePermission()

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_unauthenticated_user_cannot_create_comment(self):
        self.request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_authenticated_user_can_create_comment(self):
        self.request.user = self.user_1
        self.assertTrue(self.request.user.is_authenticated)
        self.assertTrue(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_anonymous_can_create_comment_when_anonymity_system_enabled(self):
        self.request.user = AnonymousUser()
        self.assertFalse(self.request.user.is_authenticated)
        self.assertTrue(self.permission.has_permission(self.request, self.view))


class CanBlockUsersTest(BaseAPIPermissionsTest):
    def setUp(self):
        super().setUp()
        self.request = self.factory.post('/')
        self.permission = CanBlockUsers()

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', False)
    def test_can_block_user_when_blocking_system_disabled(self):
        self.request.user = self.admin
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    def test_admin_can_block_user(self):
        self.request.user = self.admin
        self.assertTrue(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    @patch.object(settings, 'COMMENT_ALLOW_MODERATOR_TO_BLOCK', False)
    def test_moderator_cannot_block_user_when_moderation_system_disabled(self):
        self.request.user = self.moderator
        self.assertFalse(self.permission.has_permission(self.request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', True)
    @patch.object(settings, 'COMMENT_ALLOW_MODERATOR_TO_BLOCK', True)
    def test_moderator_can_block_user_when_moderation_system_enabled(self):
        self.request.user = self.moderator
        self.assertTrue(self.permission.has_permission(self.request, self.view))
