from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType

from comment.conf import settings
from comment.models import Follower
from comment.tests.base import BaseCommentTest


class FollowerModelTest(BaseCommentTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_test_follow = cls.create_comment(cls.content_object_1)
        cls.email = 't@t.com'
        cls.follower = Follower.objects.create(
            email=cls.email,
            username='test',
            content_object=cls.comment_test_follow
        )

    def test_can_create_entry(self):
        self.assertIsNotNone(self.follower)

    def test_string_value(self):
        self.assertEqual(str(self.follower), f'{str(self.comment_test_follow)} followed by {self.email}')
        self.assertEqual(repr(self.follower), f'{str(self.comment_test_follow)} followed by {self.email}')


class FollowerManagerTest(BaseCommentTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.manager = Follower.objects
        cls.follower_email = 'f1@t.com'
        cls.unfollower_email = 'uf@t.com'
        cls.comment_test_follow = cls.create_comment(cls.content_object_1)
        cls.comment_without_email = cls.create_comment(cls.content_object_1, user=cls.user_without_email)
        cls.follower = cls.manager.create(
            email=cls.follower_email,
            username='test',
            content_object=cls.comment_test_follow
        )

    def test_is_following(self):
        self.assertTrue(self.manager.is_following(self.follower_email, self.comment_test_follow))
        self.assertFalse(self.manager.is_following(self.unfollower_email, self.comment_test_follow))

    def test_follow_return_none_on_missing_email(self):
        self.assertIsNone(self.manager.follow('', 'username', self.comment_test_follow))

    def test_follow_return_none_if_email_is_already_follow(self):
        self.assertTrue(self.manager.is_following(self.follower_email, self.comment_test_follow))
        self.assertIsNone(self.manager.follow(self.follower_email, 'username', self.comment_test_follow))

    def test_follow_create_follower_instance(self):
        initial_count = self.manager.count()
        follower = self.manager.follow(self.unfollower_email, 'username', self.comment_test_follow)

        self.assertIsInstance(follower, self.manager.model)
        self.assertEqual(self.manager.count(), initial_count + 1)

    def test_unfollow_delete_follower_instance(self):
        initial_count = self.manager.count()
        self.assertTrue(self.manager.is_following(self.follower_email, self.comment_test_follow))
        self.manager.unfollow(self.follower_email, self.comment_test_follow)

        self.assertEqual(self.manager.count(), initial_count - 1)

    def test_toggle_follow_return_false_on_missing_email(self):
        email = None
        result = self.manager.toggle_follow(email=email, username='test', model_object=self.comment_test_follow)

        self.assertFalse(result)

    def test_toggle_follow_for_follower(self):
        """set the follower to unfollower and return false"""
        self.assertTrue(self.manager.is_following(self.follower_email, self.comment_test_follow))
        result = self.manager.toggle_follow(
            email=self.follower_email,
            username='test_user',
            model_object=self.comment_test_follow
        )
        self.assertFalse(result)

        self.assertFalse(self.manager.is_following(self.follower_email, self.comment_test_follow))

    def test_toggle_follow_for_unfollower(self):
        """set the unfollower to follower and return true"""
        self.assertFalse(self.manager.is_following(self.unfollower_email, self.comment_test_follow))
        result = self.manager.toggle_follow(
            email=self.unfollower_email,
            username='test_user',
            model_object=self.comment_test_follow
        )
        self.assertTrue(result)

        self.assertTrue(self.manager.is_following(self.unfollower_email, self.comment_test_follow))

    def test_follow_parent_thread_for_comment_no_email(self):
        self.assertFalse(self.comment_without_email.email)
        self.assertFalse(self.manager.is_following(self.comment_without_email.email, self.comment_without_email))
        self.manager.follow_parent_thread_for_comment(self.comment_without_email)
        self.assertFalse(self.manager.is_following(self.comment_without_email.email, self.comment_without_email))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_follow_parent_thread_for_comment_child_comment(self):
        child_comment = self.create_comment(self.content_object_1, user=self.user_2, parent=self.comment_without_email)

        # the parent (thread) will not be followed on creating child comment
        self.assertFalse(self.manager.is_following(child_comment.email, child_comment.content_object))
        # the parent comment (thread) is not followed yet
        self.assertFalse(self.manager.is_following(child_comment.email, self.comment_without_email))
        # child comment cannot be followed
        self.assertFalse(self.manager.is_following(child_comment.email, child_comment))

        self.manager.follow_parent_thread_for_comment(child_comment)

        # the parent (thread) will not be followed on creating child comment
        self.assertFalse(self.manager.is_following(child_comment.email, child_comment.content_object))
        # the parent is now followed
        self.assertTrue(self.manager.is_following(child_comment.email, self.comment_without_email))
        # child comment cannot be followed
        self.assertFalse(self.manager.is_following(child_comment.email, child_comment))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_follow_parent_thread_for_comment_parent_comment(self):
        parent_comment = self.create_comment(self.content_object_1, user=self.user_2)
        # the parent (thread) is not followed yet
        self.assertFalse(self.manager.is_following(parent_comment.email, parent_comment.content_object))
        # parent comment is not followed yet
        self.assertFalse(self.manager.is_following(parent_comment.email, parent_comment))

        self.manager.follow_parent_thread_for_comment(parent_comment)

        # the parent (thread) is now followed
        self.assertTrue(self.manager.is_following(parent_comment.email, parent_comment.content_object))
        # parent comment is now followed
        self.assertTrue(self.manager.is_following(parent_comment.email, parent_comment))

    def test_get_all_followers_for_model_object(self):
        followers = self.manager.filter_for_model_object(self.comment_test_follow)
        self.assertNotEqual(followers.count(), 0)
        content_type = ContentType.objects.get_for_model(self.comment_test_follow)

        self.assertEqual(
            list(followers),
            list(self.manager.filter(content_type=content_type, object_id=self.comment_test_follow.id))
        )

    def test_get_get_emails_for_model_object(self):
        emails = self.manager.get_emails_for_model_object(self.comment_test_follow)

        self.assertIn(self.comment_test_follow.email, emails)
