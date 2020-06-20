from time import sleep
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from comment.models import Comment, Flag, FlagInstance, Reaction, ReactionInstance
from comment.tests.base import BaseCommentManagerTest, BaseCommentTest, BaseCommentFlagTest


class CommentModelTest(BaseCommentManagerTest):
    def test_can_create_comment(self):
        parent_comment = self.create_comment(self.content_object_1)
        self.assertIsNotNone(parent_comment)
        self.assertEqual(str(parent_comment), f'comment by {parent_comment.user}: {parent_comment.content[:20]}')
        self.assertEqual(repr(parent_comment), f'comment by {parent_comment.user}: {parent_comment.content[:20]}')
        self.assertTrue(parent_comment.is_parent)
        self.assertEqual(parent_comment.replies().count(), 0)

        child_comment = self.create_comment(self.content_object_1, parent=parent_comment)
        self.assertIsNotNone(child_comment)
        self.assertEqual(str(child_comment), f'reply by {child_comment.user}: {child_comment.content[:20]}')
        self.assertEqual(repr(child_comment), f'reply by {child_comment.user}: {child_comment.content[:20]}')
        self.assertFalse(child_comment.is_parent)
        self.assertEqual(parent_comment.replies().count(), 1)

        self.assertFalse(parent_comment.is_edited)
        parent_comment.content = 'updated'
        sleep(1)
        parent_comment.save()
        self.assertTrue(parent_comment.is_edited)

    def test_replies_method(self):
        self.assertEqual(self.parent_comment_2.replies().count(), 3)

        settings.COMMENT_FLAGS_ALLOWED = 1
        reply = self.parent_comment_2.replies().first()
        self.create_flag_instance(self.user_1, reply)
        self.create_flag_instance(self.user_2, reply)
        # default replies hide flagged comment
        self.assertEqual(self.parent_comment_2.replies().count(), 2)
        self.assertEqual(self.parent_comment_2.replies(include_flagged=True).count(), 3)

    def test_reaction_signal(self):
        """Test reaction model instance is created when a comment is created"""
        parent_comment = self.create_comment(self.content_object_1)
        self.assertIsNotNone(Reaction.objects.get(comment=parent_comment))
        # 1 reaction instance is created for every comment
        self.assertEqual(Reaction.objects.count(), self.increment)

    def test_flag_signal(self):
        """Test flag model instance is created when a comment is created"""
        current_count = Flag.objects.count()
        parent_comment = self.create_comment(self.content_object_1)
        self.assertIsNotNone(Flag.objects.get(comment=parent_comment))
        # 1 flag instance is created for every comment
        self.assertEqual(Flag.objects.count(), current_count + 1)

    @patch('comment.models.comments.hasattr')
    def test_is_flagged_property(self, mocked_hasattr):
        comment = self.create_comment(self.content_object_2)
        self.assertEqual(comment.flag.state, comment.flag.UNFLAGGED)
        self.assertFalse(comment.is_flagged)

        comment.flag.state = comment.flag.FLAGGED
        self.assertTrue(comment.is_flagged)

        settings.COMMENT_FLAGS_ALLOWED = 0
        self.assertFalse(comment.is_flagged)

        mocked_hasattr.return_value = False
        self.assertFalse(comment.is_flagged)

    @patch('comment.models.comments.hasattr')
    def test_has_flagged_state(self, mocked_hasattr):
        comment = self.create_comment(self.content_object_2)
        self.assertEqual(comment.flag.state, comment.flag.UNFLAGGED)
        self.assertFalse(comment.has_flagged_state)

        comment.flag.state = comment.flag.FLAGGED
        self.assertTrue(comment.has_flagged_state)

        mocked_hasattr.return_value = False
        self.assertFalse(comment.has_flagged_state)

    @patch('comment.models.comments.hasattr')
    def test_has_rejected_state(self, mocked_hasattr):
        comment = self.create_comment(self.content_object_2)
        self.assertEqual(comment.flag.state, comment.flag.UNFLAGGED)
        self.assertFalse(comment.has_rejected_state)

        comment.flag.state = comment.flag.REJECTED
        comment.flag.save()
        self.assertTrue(comment.has_rejected_state)

        mocked_hasattr.return_value = False
        self.assertFalse(comment.has_rejected_state)

    @patch('comment.models.comments.hasattr')
    def test_has_resolved_state(self, mocked_hasattr):
        comment = self.create_comment(self.content_object_2)
        self.assertEqual(comment.flag.state, comment.flag.UNFLAGGED)
        self.assertFalse(comment.has_resolved_state)

        comment.flag.state = comment.flag.RESOLVED
        comment.flag.save()
        self.assertTrue(comment.has_resolved_state)

        mocked_hasattr.return_value = False
        self.assertFalse(comment.has_resolved_state)


class CommentModelManagerTest(BaseCommentManagerTest):

    def test_retrieve_all_parent_comments(self):
        # for all objects of a content type
        all_comments = Comment.objects.all().count()
        self.assertEqual(all_comments, 10)
        parent_comments = Comment.objects.all_parents().count()
        self.assertEqual(parent_comments, 5)

    def test_filtering_flagged_comment(self):
        settings.COMMENT_FLAGS_ALLOWED = 1
        comment = self.create_comment(self.content_object_1)
        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment - 1)

        # if COMMENT_SHOW_FLAGGED is enabled
        settings.COMMENT_SHOW_FLAGGED = True
        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)
        settings.COMMENT_SHOW_FLAGGED = False

    def test_filtering_comment_when_flag_not_enabled(self):
        settings.COMMENT_FLAGS_ALLOWED = 0
        comment = self.create_comment(self.content_object_1)
        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.count, 2)
        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)

    def test_all_comments_by_object(self):
        # all comment for a particular content type
        init_count = self.post_1.comments.count()
        self.assertEqual(init_count, 6)

        settings.COMMENT_FLAGS_ALLOWED = 1
        comment = self.post_1.comments.first()
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        # comments without flagged
        count = Comment.objects.all_comments_by_object(self.post_1).count()
        self.assertEqual(count, init_count - 1)

        # comments with flagged
        count = Comment.objects.all_comments_by_object(self.post_1, include_flagged=True).count()
        self.assertEqual(count, init_count)

    def test_filter_parents_by_object(self):
        # parent comment only
        init_count = self.post_2.comments.filter(parent=None).count()
        self.assertEqual(init_count, 2)
        settings.COMMENT_FLAGS_ALLOWED = 1
        comment = Comment.objects.filter_parents_by_object(self.post_2).first()
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        # comments without flagged
        count = Comment.objects.filter_parents_by_object(self.post_2).count()
        self.assertEqual(count, init_count - 1)

        # comments with flagged
        count = Comment.objects.filter_parents_by_object(self.post_2, include_flagged=True).count()
        self.assertEqual(count, init_count)

    def test_create_comment_by_model_type(self):
        comments = Comment.objects.all_comments_by_object(self.post_1).count()
        self.assertEqual(comments, 6)
        parent_comment = Comment.objects.create_by_model_type(
            model_type='post',
            pk=self.post_1.id,
            content='test',
            user=self.user_1
        )
        self.assertIsNotNone(parent_comment)
        comments = Comment.objects.all_comments_by_object(self.post_1).count()
        self.assertEqual(comments, 7)

        child_comment = Comment.objects.create_by_model_type(
            model_type='post',
            pk=self.post_1.id,
            content='test',
            user=self.user_1,
            parent_obj=parent_comment
        )
        self.assertIsNotNone(child_comment)
        comments = Comment.objects.all_comments_by_object(self.post_1).count()
        self.assertEqual(comments, 8)

        # fail on wrong content_type
        comment = Comment.objects.create_by_model_type(
            model_type='not exist',
            pk=self.post_1.id,
            content='test',
            user=self.user_1,
            parent_obj=parent_comment
        )
        self.assertIsNone(comment)

        # model object not exist
        comment = Comment.objects.create_by_model_type(
            model_type='post',
            pk=100,
            content='test',
            user=self.user_1,
            parent_obj=parent_comment
        )
        self.assertIsNone(comment)

    def test_create_comment_with_not_exist_model(self):
        comment = Comment.objects.create_by_model_type(
            model_type='not exist model',
            pk=self.post_1.id,
            content='test',
            user=self.user_1
        )
        self.assertIsNone(comment)


class ReactionInstanceModelTest(BaseCommentManagerTest):
    def setUp(self):
        super().setUp()
        self.user = self.user_1
        self.comment = self.child_comment_1
        self.LIKE = ReactionInstance.ReactionType.LIKE.name
        self.DISLIKE = ReactionInstance.ReactionType.DISLIKE.name

    def test_user_can_create_reaction(self):
        """Test whether reaction instance can be created"""
        instance = self.create_reaction_instance(self.user, self.comment, self.LIKE)
        self.assertIsNotNone(instance)

    def test_unique_togetherness_of_user_and_reaction_type(self):
        """Test Integrity error is raised when one user is set to have more than 1 reaction type for the same comment"""
        self.create_reaction_instance(self.user, self.comment, self.LIKE)
        self.assertRaises(IntegrityError, self.create_reaction_instance, self.user, self.comment, self.DISLIKE)

    def test_post_save_signal_increases_count_on_creation(self):
        """Test reaction count is increased on creation"""
        comment = self.comment
        self.create_reaction_instance(self.user, self.comment, self.LIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 1)
        self.assertEqual(comment.dislikes, 0)

    def test_post_delete_signal_decreases_count(self):
        """Test reaction count is decreased when an instance is deleted"""
        comment = self.comment
        instance = self.create_reaction_instance(self.user, self.comment, self.LIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 1)
        instance.delete()
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 0)

    def test_comment_property_likes_increase_and_decrease(self):
        """Test decrease and increase on likes property with subsequent request."""
        comment = self.child_comment_2
        self.create_reaction_instance(self.user, comment, self.LIKE)
        comment.refresh_from_db()
        user = self.user_2
        self.create_reaction_instance(user, comment, self.LIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 2)

        self.set_reaction(user, comment, self.LIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.likes, 1)

    def test_comment_property_dislikes_increase_and_decrease(self):
        """Test decrease and increase on dislikes property with subsequent request."""
        comment = self.child_comment_3
        self.create_reaction_instance(self.user, comment, self.DISLIKE)
        comment.refresh_from_db()
        user = self.user_2
        self.create_reaction_instance(user, comment, self.DISLIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.dislikes, 2)

        # can't use create_reaction: one user can't create multiple reaction instances for a comment.
        self.set_reaction(user, comment, self.DISLIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.dislikes, 1)

    def test_set_reaction(self):
        """Test set reactions increments the likes and dislikes property appropriately for subsequent calls"""
        comment = self.comment
        user = self.user_2
        self.set_reaction(user, comment, self.DISLIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.dislikes, 1)
        self.assertEqual(comment.likes, 0)

        self.set_reaction(user, comment, self.DISLIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.dislikes, 0)
        self.assertEqual(comment.likes, 0)

        self.set_reaction(user, comment, self.LIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.dislikes, 0)
        self.assertEqual(comment.likes, 1)

        self.set_reaction(user, comment, self.DISLIKE)
        comment.refresh_from_db()
        self.assertEqual(comment.dislikes, 1)
        self.assertEqual(comment.likes, 0)

    def test_set_reaction_on_incorrect_reaction(self):
        """Test ValidationError is raised when incorrect reaction type is passed"""
        self.assertRaises(ValidationError, self.set_reaction, self.user_1, self.child_comment_5, 'likes')


class ReactionModelTest(BaseCommentTest):
    def setUp(self):
        super().setUp()
        self.comment_1 = self.create_comment(self.content_object_1)
        self.comment_2 = self.create_comment(self.content_object_1)

    def test_reaction_count(self):
        self.assertEqual(self.comment_1.reaction.likes, 0)
        self.assertEqual(self.comment_1.reaction.dislikes, 0)

        self.comment_1.reaction.increase_reaction_count(ReactionInstance.ReactionType.LIKE.value)
        self.comment_1.reaction.refresh_from_db()

        self.assertEqual(self.comment_1.reaction.likes, 1)

        self.comment_1.reaction.increase_reaction_count(ReactionInstance.ReactionType.DISLIKE.value)
        self.comment_1.reaction.refresh_from_db()

        self.assertEqual(self.comment_1.reaction.dislikes, 1)

        self.comment_1.reaction.decrease_reaction_count(ReactionInstance.ReactionType.LIKE.value)
        self.comment_1.reaction.refresh_from_db()

        self.assertEqual(self.comment_1.reaction.likes, 0)

        self.comment_1.reaction.decrease_reaction_count(ReactionInstance.ReactionType.DISLIKE.value)
        self.comment_1.reaction.refresh_from_db()

        self.assertEqual(self.comment_1.reaction.dislikes, 0)

    def test_increase_reaction_signal(self):
        self.assertEqual(self.comment_1.reaction.likes, 0)
        # reaction instance created
        reaction_instance = ReactionInstance.objects.create(
            reaction=self.comment_1.reaction, user=self.user_1, reaction_type=1)
        self.comment_1.reaction.refresh_from_db()
        self.assertEqual(self.comment_1.reaction.likes, 1)
        self.assertEqual(self.comment_1.reaction.dislikes, 0)

        # edit reaction instance won't change reaction count
        reaction_instance.reaction_type = 2  # dislike
        reaction_instance.save()
        self.comment_1.reaction.refresh_from_db()
        self.assertEqual(self.comment_1.reaction.likes, 1)
        self.assertEqual(self.comment_1.reaction.dislikes, 0)


class ReactionInstanceManagerTest(BaseCommentTest):
    def test_clean_reaction_type(self):
        LIKE = ReactionInstance.ReactionType.LIKE
        # valid reaction type
        reaction_type = ReactionInstance.objects.clean_reaction_type(LIKE.name)
        self.assertEqual(reaction_type, LIKE.value)

        # invalid reaction type
        self.assertRaises(ValidationError, ReactionInstance.objects.clean_reaction_type, 1)

        # invalid reaction type
        self.assertRaises(ValidationError, ReactionInstance.objects.clean_reaction_type, 'likes')


class FlagInstanceModelTest(BaseCommentFlagTest):
    def test_create_flag(self):
        data = self.flag_data
        comment = self.comment
        instance = self.create_flag_instance(self.user, comment, **data)
        self.assertIsNotNone(instance)
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)

    def test_post_delete_signal_decreases_count(self):
        """Test flag count is decreased when an instance is deleted"""
        data = self.flag_data
        comment = self.comment
        instance = self.create_flag_instance(self.user, comment, **data)
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)
        instance.delete()
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 0)

    def test_post_save_signal_increases_count_on_creation(self):
        comment = self.comment
        self.create_flag_instance(self.user, comment)
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)


class FlagInstanceManagerTest(BaseCommentFlagTest):
    def setUp(self):
        super().setUp()

    def test_clean_reason_for_invalid_value(self):
        data = self.flag_data
        data.update({'reason': -1})
        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **data)

        data.update({'reason': 'abcd'})
        self.assertRaises(ValidationError, self.set_flag, self.user, self.comment, **data)

    def test_clean_for_invalid_values(self):
        data = self.flag_data
        user = self.user
        comment = self.comment
        # info can't be blank with the last reason(something else)
        data.update({'reason': FlagInstance.objects.reason_values[-1]})
        self.assertRaises(ValidationError, self.set_flag, user, comment, **data)

        data.pop('reason')
        self.assertRaises(ValidationError, self.set_flag, user, comment, **data)

    def test_clean_ignores_info_for_all_reasons_except_last(self):
        data = self.flag_data
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

    def test_unflag_non_exist_flag(self):
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

    def test_increase_flag_signal(self):
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

    def test_is_flagged_enabled(self):
        flag = self.create_comment(self.content_object_1).flag
        settings.COMMENT_FLAGS_ALLOWED = 1
        self.assertTrue(flag.is_flag_enabled)

        settings.COMMENT_FLAGS_ALLOWED = 0
        self.assertFalse(flag.is_flag_enabled)

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

        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        flag.refresh_from_db()
        self.assertEqual(flag.count, 2)

        # flagging is disabled => state won't change
        settings.COMMENT_FLAGS_ALLOWED = 0
        flag.toggle_flagged_state()
        self.assertEqual(flag.state, flag.UNFLAGGED)

        # flagging is enabled => state changes
        settings.COMMENT_FLAGS_ALLOWED = 1
        flag.toggle_flagged_state()
        self.assertEqual(flag.state, flag.FLAGGED)

        # increase allowed flags count => change the state to UNFLAGGED
        settings.COMMENT_FLAGS_ALLOWED = 10
        self.assertEqual(flag.count, 2)
        flag.toggle_flagged_state()
        self.assertEqual(flag.state, flag.UNFLAGGED)
