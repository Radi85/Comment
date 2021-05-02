from time import sleep
from unittest.mock import patch

from django.utils import timezone

from comment.conf import settings
from comment.models import Comment
from comment.tests.base import BaseCommentManagerTest, RequestFactory


class CommentModelTest(BaseCommentManagerTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.parent_comment = cls.create_comment(cls.content_object_1)

    def test_parent_comment_properties(self):
        comment = self.parent_comment

        self.assertIsNotNone(comment)
        self.assertEqual(str(comment), f'comment by {comment.user}: {comment.content[:20]}')
        self.assertEqual(repr(comment), f'comment by {comment.user}: {comment.content[:20]}')
        self.assertTrue(comment.is_parent)
        self.assertEqual(comment.replies().count(), 0)
        self.assertIsNotNone(comment.urlhash)

    def test_child_comment_properties(self):
        comment = self.create_comment(self.content_object_1, parent=self.parent_comment)

        self.assertIsNotNone(comment)
        self.assertEqual(str(comment), f'reply by {comment.user}: {comment.content[:20]}')
        self.assertEqual(repr(comment), f'reply by {comment.user}: {comment.content[:20]}')
        self.assertFalse(comment.is_parent)
        self.assertEqual(self.parent_comment.replies().count(), 1)
        self.assertIsNotNone(comment.urlhash)

    def test_is_edited(self):
        comment = self.create_comment(self.content_object_1)
        self.assertFalse(comment.is_edited)

        comment.content = 'updated'
        sleep(1)
        comment.save()

        self.assertTrue(comment.is_edited)

    def test_is_edited_for_anonymous_comment(self):
        comment = self.create_anonymous_comment(posted=timezone.now() - timezone.timedelta(days=1))

        self.assertFalse(comment.is_edited)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    @patch.object(settings, 'COMMENT_SHOW_FLAGGED', False)
    def test_replies_method_without_any_flags(self):
        init_count = self.parent_comment_2.replies().count()
        reply = self.parent_comment_2.replies().first()

        self.create_flag_instance(self.user_1, reply)
        self.create_flag_instance(self.user_2, reply)

        # default replies method hides flagged comment
        self.assertEqual(self.parent_comment_2.replies(include_flagged=True).count(), init_count)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    @patch.object(settings, 'COMMENT_SHOW_FLAGGED', False)
    def test_replies_method_with_flags(self):
        init_count = self.parent_comment_2.replies().count()
        reply = self.parent_comment_2.replies().first()

        self.create_flag_instance(self.user_1, reply)
        self.create_flag_instance(self.user_2, reply)

        # the comment is hidden, since it is flagged.
        self.assertEqual(self.parent_comment_2.replies().count(), init_count - 1)

    @patch('comment.models.comments.hasattr')
    def test_is_flagged_property(self, mocked_hasattr):
        comment = self.create_comment(self.content_object_2)
        self.assertEqual(comment.flag.state, comment.flag.UNFLAGGED)
        self.assertFalse(comment.is_flagged)

        comment.flag.state = comment.flag.FLAGGED
        self.assertTrue(comment.is_flagged)

        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0):
            self.assertIs(False, comment.is_flagged)

            mocked_hasattr.return_value = False
            self.assertIs(False, comment.is_flagged)

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

    @patch('comment.managers.CommentManager.generate_urlhash')
    def test_urlhash_is_unique(self, mocked_generate_urlhash):
        mocked_generate_urlhash.side_effect = ['first_urlhash', 'first_urlhash', 'second_urlhash']
        first_comment = self.create_comment(self.content_object_1)

        self.assertEqual(first_comment.urlhash, 'first_urlhash')

        mocked_generate_urlhash.assert_called_once()
        second_comment = self.create_comment(self.content_object_1)

        self.assertEqual(second_comment.urlhash, 'second_urlhash')
        self.assertEqual(mocked_generate_urlhash.call_count, 3)

    def test_comment_email(self):
        comment = self.parent_comment_1

        self.assertEqual(comment.email, comment.user.email)

    def test_get_username_for_non_anonymous_comment(self):
        comment = self.create_comment(self.content_object_1, user=self.user_1)

        self.assertEqual(comment.get_username(), comment.user.username)

    def test_get_username_for_anonymous_comment(self):
        comment = self.create_anonymous_comment()

        with patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', False):
            self.assertEqual(comment.get_username(), settings.COMMENT_ANONYMOUS_USERNAME)

        with patch.object(settings, 'COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME', True):
            self.assertEqual(comment.get_username(), comment.email.split('@')[0])


class CommentModelManagerTest(BaseCommentManagerTest):

    def test_retrieve_all_parent_comments(self):
        # for all objects of a content type
        all_comments = Comment.objects.all().count()

        self.assertEqual(all_comments, 10)

        parent_comments = Comment.objects.all_parents().count()

        self.assertEqual(parent_comments, 5)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_filtering_flagged_comment(self):
        comment = self.parent_comment_1
        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)

        with patch.object(settings, 'COMMENT_SHOW_FLAGGED', False):
            self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment - 1)

        with patch.object(settings, 'COMMENT_SHOW_FLAGGED', True):
            self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_filtering_comment_when_flag_not_enabled(self):
        comment = self.parent_comment_1
        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.count, 2)

        self.assertEqual(Comment.objects.all_exclude_flagged().count(), self.increment)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    @patch.object(settings, 'COMMENT_SHOW_FLAGGED', False)
    def test_all_comments_by_object(self):
        # all comment for a particular content type
        init_count = self.post_1.comments.count()
        self.assertEqual(init_count, 6)

        comment = self.post_1.comments.first()
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        # comments without flagged
        count = Comment.objects.all_comments_by_object(self.post_1).count()
        self.assertEqual(count, init_count - 1)

        # comments with flagged
        count = Comment.objects.all_comments_by_object(self.post_1, include_flagged=True).count()

        self.assertEqual(count, init_count)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    @patch.object(settings, 'COMMENT_SHOW_FLAGGED', False)
    def test_filter_parents_by_object(self):
        # parent comment only
        init_count = self.post_2.comments.filter(parent=None).count()
        self.assertEqual(init_count, 2)
        comment = Comment.objects.filter_parents_by_object(self.post_2).first()
        self.create_flag_instance(self.user_1, comment)
        self.create_flag_instance(self.user_2, comment)
        # comments without flagged
        count = Comment.objects.filter_parents_by_object(self.post_2).count()

        self.assertEqual(count, init_count - 1)

        # comments with flagged
        count = Comment.objects.filter_parents_by_object(self.post_2, include_flagged=True).count()

        self.assertEqual(count, init_count)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    @patch.object(settings, 'COMMENT_SHOW_FLAGGED', False)
    def test_get_parent_comment(self):
        # no parent_id passed from the url
        self.assertIsNone(Comment.objects.get_parent_comment(''))
        # no parent_id passed as 0
        self.assertIsNone(Comment.objects.get_parent_comment('0'))
        # no parent_id doesn't exist passed -> although this is highly unlikely as this will be handled by the mixin
        # but is useful for admin interface if required
        self.assertIsNone(Comment.objects.get_parent_comment(100))
        parent_comment = Comment.objects.get_parent_comment(self.parent_comment_1.id)
        self.assertIsNotNone(parent_comment)
        self.assertEqual(parent_comment, self.parent_comment_1)


class OrderForParentCommentsTest(BaseCommentManagerTest):
    def setUp(self):
        super().setUp()
        self.all_parents_qs = Comment.objects.all_exclude_flagged().filter(parent=None)
        self.all_comments_qs = Comment.objects.all_exclude_flagged()

    def test_default_value(self):
        self.assertQuerysetEqual(
            Comment.objects._filter_parents(self.all_comments_qs),
            self.all_parents_qs.order_by(*settings.COMMENT_ORDER_BY)
            )

    @patch.object(settings, 'COMMENT_ORDER_BY', ['-reaction__likes'])
    def test_custom_values(self):
        self.assertQuerysetEqual(
            Comment.objects._filter_parents(self.all_comments_qs),
            self.all_parents_qs.order_by(*settings.COMMENT_ORDER_BY)
            )


class GetUrlTest(BaseCommentManagerTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.request = RequestFactory().get('/')
        cls.request.user = cls.user_1
        # no pagination(parent comment 3, 2, 1 belong to the same content_object_1)

    @patch.object(settings, 'COMMENT_PER_PAGE', 0)
    def test_with_pagination_disabled(self):
        comment = self.parent_comment_3
        comment_url = comment.content_object.get_absolute_url() + '#' + comment.urlhash

        self.assertEqual(comment_url, comment.get_url(self.request))

    @patch.object(settings, 'COMMENT_PER_PAGE', 3)
    def test_comment_on_first_page(self):
        comment = self.parent_comment_3
        comment_url = comment.content_object.get_absolute_url() + '#' + comment.urlhash
        self.assertEqual(comment_url, comment.get_url(self.request))

    @patch.object(settings, 'COMMENT_PER_PAGE', 3)
    def test_comment_not_on_first_page(self):
        comment = self.parent_comment_1
        comment_url = comment.content_object.get_absolute_url() + '?page=2' + '#' + comment.urlhash
        self.assertEqual(comment_url, comment.get_url(self.request))
