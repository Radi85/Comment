from unittest.mock import patch

from comment.signals import adjust_flagged_comments
from comment.tests.base import BaseCommentSignalTest
from comment.models import Comment, Flag, FlagInstance, Reaction, ReactionInstance
from comment.conf import settings


class TestPostMigrate(BaseCommentSignalTest):
    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_adjust_flagged_comments(self):
        comment_1 = self.create_comment(self.content_object_1)
        comment_2 = self.create_comment(self.content_object_2)
        self.assertFalse(comment_1.is_flagged)
        self.assertFalse(comment_2.is_flagged)

        self.create_flag_instance(self.user_1, comment_1)
        self.create_flag_instance(self.user_2, comment_1)

        self.create_flag_instance(self.user_1, comment_2)
        self.create_flag_instance(self.user_2, comment_2)

        # flagged comment with wrong state will be adjusted
        comment_1.flag.state = comment_1.flag.UNFLAGGED
        comment_1.flag.save()
        comment_1.flag.refresh_from_db()
        self.assertEqual(comment_1.flag.count, 2)
        self.assertEqual(comment_1.flag.state, comment_1.flag.UNFLAGGED)
        self.assertFalse(comment_1.is_flagged)

        # flagged comment with right state => will be skipped
        comment_2.flag.refresh_from_db()
        self.assertEqual(comment_2.flag.count, 2)
        self.assertEqual(comment_2.flag.state, comment_2.flag.FLAGGED)
        self.assertTrue(comment_2.is_flagged)

        adjust_flagged_comments(self)
        comment_1.flag.refresh_from_db()
        self.assertEqual(comment_1.flag.count, 2)
        self.assertTrue(comment_1.is_flagged)


class TestPostSave(BaseCommentSignalTest):
    def test_reaction_signal(self):
        """Test reaction model instance is created when a comment is created"""
        parent_comment = self.create_comment(self.content_object_1)
        self.assertIsNotNone(Reaction.objects.get(comment=parent_comment))
        # 1 reaction instance is created for every comment
        self.assertEqual(Reaction.objects.count(), Comment.objects.count())

    def test_flag_signal(self):
        """Test flag model instance is created when a comment is created"""
        current_count = Flag.objects.count()
        parent_comment = self.create_comment(self.content_object_1)
        self.assertIsNotNone(Flag.objects.get(comment=parent_comment))
        # 1 flag instance is created for every comment
        self.assertEqual(Flag.objects.count(), current_count + 1)

    def test_increase_reaction_count(self):
        comment = self.comment
        self.assertEqual(comment.reaction.likes, 0)
        # reaction instance created
        reaction_instance = ReactionInstance.objects.create(
            reaction=comment.reaction, user=self.user_1, reaction_type=self.LIKE.value)
        comment.reaction.refresh_from_db()
        self.assertEqual(comment.reaction.likes, 1)
        self.assertEqual(comment.reaction.dislikes, 0)

        # edit reaction instance won't change reaction count
        reaction_instance.reaction_type = self.DISLIKE.value
        reaction_instance.save()
        comment.reaction.refresh_from_db()
        self.assertEqual(comment.reaction.likes, 1)
        self.assertEqual(comment.reaction.dislikes, 0)

    def test_increase_flag_count(self):
        self.assertEqual(self.comment.flag.count, 0)
        # instance created
        self.set_flag(self.user, self.comment, **self.flag_data)
        self.comment.flag.refresh_from_db()
        self.assertEqual(self.comment.flag.count, 1)
        # instance edited won't increase the flag count
        flag_instance = FlagInstance.objects.get(user=self.user, flag__comment=self.comment)
        self.assertIsNotNone(flag_instance)
        flag_instance.info = 'change value for test'
        flag_instance.save()
        self.comment.flag.refresh_from_db()
        self.assertEqual(self.comment.flag.count, 1)


class TestPostDelete(BaseCommentSignalTest):
    def test_reaction_decrease_count(self):
        """Test reaction count is decreased when an instance is deleted"""
        comment = self.comment
        instance = self.create_reaction_instance(self.user, self.comment, self.LIKE.name)
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 1)
        instance.delete()
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 0)

    def test_flag_decrease_count(self):
        """Test flag count is decreased when an instance is deleted"""
        data = self.flag_data
        comment = self.comment
        instance = self.create_flag_instance(self.user, comment, **data)
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)
        instance.delete()
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 0)
