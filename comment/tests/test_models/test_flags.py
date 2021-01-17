from unittest.mock import patch

from django.core.exceptions import ValidationError

from comment.conf import settings
from comment.models import FlagInstance
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

        data.update({'reason': 'abc'})
        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **data)

    def test_clean_for_invalid_values(self):
        data = self.flag_data.copy()
        user = self.user
        comment = self.comment
        # info can't be blank with the last reason(something else)
        data.update({'reason': FlagInstance.objects.reason_values[-1]})
        self.assertRaises(ValidationError, self.set_flag, user, comment, **data)

        data.pop('reason')
        self.assertRaises(ValidationError, self.set_flag, user, comment, **data)

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

    def test_un_flag_non_exist_flag(self):
        # user try to un-flag comment that wasn't flagged yet
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

    def test_is_flagged_enabled(self):
        flag = self.create_comment(self.content_object_1).flag
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1):
            self.assertIs(True, flag.is_flag_enabled)

        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0):
            self.assertIs(False, flag.is_flag_enabled)

    @patch('comment.models.flags.Flag.get_clean_state')
    def test_get_verbose_state(self, mocked_get_clean_state):
        flag = self.create_comment(self.content_object_1).flag
        mocked_get_clean_state.return_value = flag.FLAGGED
        self.assertEqual(flag.get_verbose_state(flag.FLAGGED), flag.STATES_CHOICES[flag.FLAGGED-1][1])
        mocked_get_clean_state.return_value = 100
        self.assertIsNone(flag.get_verbose_state(100))

    def test_get_clean_state(self):
        flag = self.create_comment(self.content_object_1).flag
        state = flag.get_clean_state(flag.FLAGGED)
        self.assertEqual(state, 2)

        # int not in existing states
        self.assertRaises(ValidationError, flag.get_clean_state, 100)

        # not int
        self.assertRaises(ValidationError, flag.get_clean_state, 'Not int')

        # None
        self.assertRaises(ValidationError, flag.get_clean_state, None)

    def test_toggle_state(self):
        flag = self.create_comment(self.content_object_1).flag
        self.assertIsNone(flag.moderator)
        self.assertEqual(flag.state, flag.UNFLAGGED)

        # toggle states occurs between rejected and resolved only
        self.assertRaises(ValidationError, flag.toggle_state, flag.FLAGGED, self.moderator)

        flag.toggle_state(flag.REJECTED, self.moderator)
        self.assertEqual(flag.state, flag.REJECTED)
        self.assertEqual(flag.moderator, self.moderator)

        # passing RESOLVED state value for the first time
        flag.toggle_state(flag.RESOLVED, self.moderator)
        self.assertEqual(flag.state, flag.RESOLVED)

        # passing RESOLVED state value for the second time
        flag.toggle_state(flag.RESOLVED, self.moderator)
        # state reset to FLAGGED
        self.assertEqual(flag.state, flag.FLAGGED)

    def test_toggle_flagged_state(self):
        comment = self.create_comment(self.content_object_1)
        flag = comment.flag
        flag.toggle_flagged_state()
        self.assertEqual(flag.state, flag.UNFLAGGED)

        # TODO split this test to be independent from the actual settings
        # current settings value COMMENT_FLAGS_ALLOWED = 2
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        flag.refresh_from_db()
        self.assertEqual(flag.count, 2)

        # flagging is disabled => state won't change
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0):
            flag.toggle_flagged_state()
            self.assertEqual(flag.state, flag.UNFLAGGED)

        # flagging is enabled => state changes
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1):
            flag.toggle_flagged_state()
            self.assertEqual(flag.state, flag.FLAGGED)

        # increase allowed flags count => change the state to UNFLAGGED
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 10):
            self.assertEqual(flag.count, 2)
            flag.toggle_flagged_state()
            self.assertEqual(flag.state, flag.UNFLAGGED)
