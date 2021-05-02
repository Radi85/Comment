from unittest.mock import patch

from comment.models import BlockedUser
from comment.tests.base import BaseBlockerManagerTest
from comment.conf import settings


class BlockerModelTest(BaseBlockerManagerTest):

    def test_blocked_user_str(self):
        self.assertEqual(str(self.blocked_user_by_id), self.blocked_user_by_id.user.username)

    def test_blocked_email_str(self):
        self.assertEqual(str(self.blocked_user_by_email), self.blocked_user_by_email.email)


class BlockerManagerTest(BaseBlockerManagerTest):
    @patch.object(settings, 'COMMENT_ALLOW_BLOCKING_USERS', False)
    def test_is_user_blocked_when_system_disabled(self):
        self.assertFalse(BlockedUser.objects.is_user_blocked(email=self.blocked_email))

    def test_is_user_blocked_by_id_invalid_id(self):
        self.assertFalse(BlockedUser.objects._is_user_blocked_by_id(None))

    def test_is_user_blocked_by_email_for_none_value(self):
        self.assertFalse(BlockedUser.objects._is_user_blocked_by_email(None))

    def test_is_user_blocked_for_blocked_user(self):
        self.assertTrue(BlockedUser.objects.is_user_blocked(user_id=self.blocked_user.id))

    def test_is_user_blocked_for_unblocked_user(self):
        self.assertFalse(BlockedUser.objects.is_user_blocked(user_id=self.user_1.id))

    def test_is_user_blocked_for_none_values(self):
        self.assertFalse(BlockedUser.objects.is_user_blocked())

    def test_is_user_blocked_for_blocked_email(self):
        self.assertTrue(BlockedUser.objects.is_user_blocked(email=self.blocked_email))

    def test_is_user_blocked_for_unblocked_email(self):
        self.assertFalse(BlockedUser.objects.is_user_blocked(email='unblocked@test.com'))

    def test_get_blocked_user_by_user_id_when_already_exists(self):
        blocked_user, created = BlockedUser.objects._get_or_create_blocked_user_by_user_id(self.blocked_user.id)
        self.assertFalse(created)

    def test_create_blocked_user_by_user_id(self):
        blocked_user, created = BlockedUser.objects._get_or_create_blocked_user_by_user_id(self.unblocked_user.id)
        self.assertTrue(created)

    def test_get_blocked_user_by_email_when_already_exists(self):
        blocked_user, created = BlockedUser.objects._get_or_create_blocked_user_by_email(self.blocked_email)
        self.assertFalse(created)

    def test_create_blocked_user_by_email(self):
        blocked_user, created = BlockedUser.objects._get_or_create_blocked_user_by_email('test@test.com')
        self.assertTrue(created)

    @patch('comment.managers.BlockedUserManager.get_or_create')
    def test_get_blocked_user_by_email_for_multiple_entries(self, mocked_get_or_create):
        mocked_get_or_create.side_effect = BlockedUser.MultipleObjectsReturned
        blocked_user, created = BlockedUser.objects._get_or_create_blocked_user_by_email('test@test.com')
        self.assertFalse(created)
