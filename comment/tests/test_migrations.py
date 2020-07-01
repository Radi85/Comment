from unittest.mock import patch

from django.apps import apps

from comment.conf import settings
from comment.apps import adjust_flagged_comments
from comment.tests.base import BaseCommentTest, BaseCommentMigrationTest


class MigrationTest(BaseCommentTest):
    def test_adjust_flagged_comments(self):
        settings.COMMENT_FLAGS_ALLOWED = 1
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
        self.assertTrue(comment_1.flag.count, 2)
        self.assertEqual(comment_1.flag.state, comment_1.flag.UNFLAGGED)
        self.assertFalse(comment_1.is_flagged)

        # flagged comment with right state => will be kipped
        comment_2.flag.refresh_from_db()
        self.assertTrue(comment_2.flag.count, 2)
        self.assertEqual(comment_2.flag.state, comment_2.flag.FLAGGED)
        self.assertTrue(comment_2.is_flagged)

        adjust_flagged_comments(self)
        comment_1.flag.refresh_from_db()
        self.assertTrue(comment_1.flag.count, 2)
        self.assertTrue(comment_1.is_flagged)


class CommentURLHashMigrationTest(BaseCommentMigrationTest):
    migrate_from = '0007_auto_20200620_1259'
    migrate_to = '0008_comment_urlhash'

    def setUp(self):
        super().setUp()
        self.current_model = apps.get_model('comment', 'Comment')

    def create_comment(self):
        self.instance += 1
        return self.previous_model.objects.create(
            content_type_id=self.ct_object.id,
            object_id=self.instance,
            content=f'test urlhash - {self.instance}',
            user_id=self.user.id
        )

    def setUpBeforeMigration(self, apps):
        self.instance = 0
        self.previous_model = apps.get_model('comment', 'Comment')
        self.comment = self.create_comment()

    def test_urlhash_migrated(self):
        comment = self.current_model.objects.get(id=self.comment.id)
        
        self.assertIsNotNone(comment.urlhash)
