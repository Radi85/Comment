from unittest.mock import patch

from django.core.exceptions import ValidationError

from comment.conf import settings
from comment.models import FlagInstance, Flag
from comment.tests.base import BaseCommentFlagTest


class FlagInstanceModelTest(BaseCommentFlagTest):
    def test_create_flag(self):
        data = self.flag_data
        comment = self.comment
        instance = self.create_flag_instance(self.user, comment, **data)

        self.assertIsNotNone(instance)
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)


class FlagInstanceManagerTest(BaseCommentFlagTest):
    def test_clean_reason_for_invalid_value(self):
        data = self.flag_data.copy()
        data.update({'reason': -1})

        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **data)

    def test_clean_reason_for_wrong_type(self):
        data = self.flag_data.copy()
        data.update({'reason': 'abc'})

        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **data)

    def test_clean_for_last_reason_without_info(self):
        data = self.flag_data.copy()
        data.update({'reason': FlagInstance.objects.reason_values[-1]})

        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **data)

    def test_clean_without_reason(self):
        data = self.flag_data.copy()
        data.pop('reason')

        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **data)

    def test_clean_ignores_info_for_all_reasons_except_last(self):
        data = self.flag_data.copy()
        info = 'Hi'
        data['info'] = info
        user = self.user
        comment = self.comment
        self.set_flag(user, comment, **data)
        instance = FlagInstance.objects.get(user=user, flag=comment.flag)

        self.assertIsNone(instance.info)

        new_comment = self.create_comment(self.content_object_1)
        data['reason'] = FlagInstance.objects.reason_values[-1]
        self.set_flag(user, new_comment, **data)
        instance = FlagInstance.objects.get(user=user, flag=new_comment.flag)

        self.assertEqual(instance.info, info)

    def test_set_flag_for_create(self):
        self.assertTrue(self.set_flag(self.user, self.comment, **self.flag_data))

    def test_set_flag_for_delete(self):
        self.assertFalse(self.set_flag(self.user_2, self.comment_2))

    def test_create_flag_twice(self):
        self.assertTrue(self.set_flag(self.user, self.comment, **self.flag_data))

        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **self.flag_data)

    def test_un_flag_non_existent_flag(self):
        # user tries to un-flag comment that wasn't flagged yet
        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment)


class FlagModelTest(BaseCommentFlagTest):
    def test_flag_count(self):
        comment = self.comment

        self.assertEqual(comment.flag.count, 0)

        comment.flag.increase_count()
        comment.refresh_from_db()

        self.assertEqual(comment.flag.count, 1)

        comment.flag.decrease_count()
        comment.flag.refresh_from_db()

        self.assertEqual(comment.flag.count, 0)

    def test_comment_author(self):
        comment = self.comment

        self.assertEqual(comment.user, comment.flag.comment_author)


class ToggleFlaggedStateTest(BaseCommentFlagTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_comment(cls.content_object_1)
        cls.flag = cls.comment.flag
        cls.create_flag_instance(cls.user_1, cls.comment)
        cls.create_flag_instance(cls.user_2, cls.comment)
        cls.flag.refresh_from_db()

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_flag_disabled_with_flag_count_greater_than_allowed_count(self):
        self.flag.state = self.flag.UNFLAGGED
        self.flag.save()
        self.flag.refresh_from_db()

        # verify that number of flags on the object is greater than the allowed flags
        assert self.flag.count > settings.COMMENT_FLAGS_ALLOWED
        self.flag.toggle_flagged_state()

        self.assertEqual(self.flag.state, self.flag.UNFLAGGED)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_when_flagging_is_enabled(self):
        self.flag.toggle_flagged_state()

        self.assertEqual(self.flag.state, self.flag.FLAGGED)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 10)
    def test_with_large_allowed_flag_count(self):
        self.assertEqual(self.flag.count, 2)
        self.flag.toggle_flagged_state()

        self.assertEqual(self.flag.state, self.flag.UNFLAGGED)


class ToggleStateTest(BaseCommentFlagTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag = cls.create_comment(cls.content_object_1).flag

    def test_unflagged_state(self):
        # toggle states occurs between rejected and resolved only
        self.assertRaises(ValidationError, self.flag.toggle_state, self.flag.FLAGGED, self.moderator)

    def test_rejected_state(self):
        self.flag.toggle_state(self.flag.REJECTED, self.moderator)

        self.assertEqual(self.flag.state, self.flag.REJECTED)
        self.assertEqual(self.flag.moderator, self.moderator)

    def test_passing_same_state_twice(self):
        # passing RESOLVED state value for the first time
        self.flag.toggle_state(self.flag.RESOLVED, self.moderator)
        self.assertEqual(self.flag.state, self.flag.RESOLVED)

        # passing RESOLVED state value for the second time
        self.flag.toggle_state(self.flag.RESOLVED, self.moderator)
        # state reset to FLAGGED
        self.assertEqual(self.flag.state, self.flag.FLAGGED)


class GetVerboseStateTest(BaseCommentFlagTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag = cls.create_comment(cls.content_object_1).flag

    @patch('comment.models.flags.Flag.get_clean_state')
    def test_valid_state(self, mocked_get_clean_state):
        mocked_get_clean_state.return_value = self.flag.FLAGGED

        self.assertEqual(
            self.flag.get_verbose_state(self.flag.FLAGGED),
            self.flag.STATES_CHOICES[self.flag.FLAGGED-1][1],
        )

    @patch('comment.models.flags.Flag.get_clean_state')
    def test_invalid_state(self, mocked_get_clean_state):
        mocked_get_clean_state.return_value = 100

        self.assertIsNone(self.flag.get_verbose_state(100))


class GetCleanStateTest(BaseCommentFlagTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag = cls.create_comment(cls.content_object_1).flag

    def test_valid_state(self):
        state = self.flag.get_clean_state(self.flag.FLAGGED)

        self.assertEqual(state, Flag.FLAGGED)

    def test_invalid_int(self):
        self.assertRaises(ValidationError, self.flag.get_clean_state, 100)

    def test_non_integeral_value(self):
        self.assertRaises(ValidationError, self.flag.get_clean_state, 'Not int')

    def test_passing_none(self):
        self.assertRaises(ValidationError, self.flag.get_clean_state, None)


class IsFlagEnabledTest(BaseCommentFlagTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag = cls.create_comment(cls.content_object_1).flag

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_when_enabled(self):
        self.assertIs(True, self.flag.is_flag_enabled)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_when_disabled(self):
        self.assertIs(False, self.flag.is_flag_enabled)
