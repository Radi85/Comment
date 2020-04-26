from time import sleep
from comment.models import Comment
from comment.tests.base import BaseCommentTest


class CommentModelTest(BaseCommentTest):
    def test_can_create_comment(self):
        parent_comment = self.create_comment(self.content_object_1)
        self.assertIsNotNone(parent_comment)
        self.assertEqual(str(parent_comment), f'comment by {parent_comment.user}: {parent_comment.content[:20]}')
        self.assertEqual(repr(parent_comment), f'comment by {parent_comment.user}: {parent_comment.content[:20]}')
        self.assertEqual(parent_comment.replies.count(), 0)

        child_comment = self.create_comment(self.content_object_1, parent=parent_comment)
        self.assertIsNotNone(child_comment)
        self.assertEqual(str(child_comment), f'reply by {child_comment.user}: {child_comment.content[:20]}')
        self.assertEqual(repr(child_comment), f'reply by {child_comment.user}: {child_comment.content[:20]}')
        self.assertEqual(parent_comment.replies.count(), 1)

        self.assertFalse(parent_comment.is_edited)
        parent_comment.content = 'updated'
        sleep(1)
        parent_comment.save()
        self.assertTrue(parent_comment.is_edited)


class CommentModelManagerTest(BaseCommentTest):
    def setUp(self):
        super().setUp()
        self.parent_comment_1 = self.create_comment(self.content_object_1)
        self.parent_comment_2 = self.create_comment(self.content_object_1)
        self.parent_comment_3 = self.create_comment(self.content_object_1)
        self.child_comment_1 = self.create_comment(self.content_object_1, parent=self.parent_comment_1)
        self.child_comment_2 = self.create_comment(self.content_object_1, parent=self.parent_comment_2)
        self.child_comment_3 = self.create_comment(self.content_object_1, parent=self.parent_comment_2)

        self.parent_comment_4 = self.create_comment(self.content_object_2)
        self.parent_comment_5 = self.create_comment(self.content_object_2)
        self.child_comment_4 = self.create_comment(self.content_object_2, parent=self.parent_comment_1)
        self.child_comment_5 = self.create_comment(self.content_object_2, parent=self.parent_comment_2)

    def test_retrieve_all_parent_comments(self):
        # for all objects of a content type
        all_comments = Comment.objects.all().count()
        self.assertEqual(all_comments, 10)
        parent_comments = Comment.objects.all_parent_comments().count()
        self.assertEqual(parent_comments, 5)

    def test_filter_comments_by_object(self):
        # parent comment only
        comments = Comment.objects.filter_parents_by_object(self.post_2).count()
        self.assertEqual(comments, 2)

    def test_all_comments(self):
        # all comment for a particular content type
        comments = Comment.objects.all_comments_by_objects(self.post_1).count()
        self.assertEqual(comments, 6)

    def test_create_comment_by_model_type(self):
        comments = Comment.objects.all_comments_by_objects(self.post_1).count()
        self.assertEqual(comments, 6)
        parent_comment = Comment.objects.create_by_model_type(
            model_type='post',
            pk=self.post_1.id,
            content='test',
            user=self.user_1
        )
        self.assertIsNotNone(parent_comment)
        comments = Comment.objects.all_comments_by_objects(self.post_1).count()
        self.assertEqual(comments, 7)

        child_comment = Comment.objects.create_by_model_type(
            model_type='post',
            pk=self.post_1.id,
            content='test',
            user=self.user_1,
            parent_obj=parent_comment
        )
        self.assertIsNotNone(child_comment)
        comments = Comment.objects.all_comments_by_objects(self.post_1).count()
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
