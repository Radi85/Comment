from comment.tests.base import BaseCommentMigrationTest


class CommentMigrationTest(BaseCommentMigrationTest):
    migrate_from = '0007_auto_20200620_1259'
    migrate_to = '0009_auto_20200811_1945'

    def create_comment(self):
        self.instance += 1
        return self.old_model.objects.create(
            content_type_id=self.ct_object.id,
            object_id=self.instance,
            content=f'test migration - {self.instance}',
            user_id=self.user.id,
        )

    def setUpBeforeMigration(self, apps):
        self.instance = 0
        self.comment = self.create_comment()

    def test_email_and_urlhash_migrated(self):
        comment = self.new_model.objects.get(id=self.comment.id)

        self.assertEqual(hasattr(comment, 'urlhash'), True)
        self.assertEqual(comment.email, comment.user.email)
