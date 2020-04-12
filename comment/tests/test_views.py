from django.urls import reverse

from comment.models import Comment
from comment.tests.base import BaseCommentTest


class CreateCommentTestCase(BaseCommentTest):

    def test_create_comment(self):
        all_comments = Comment.objects.all().count()
        parent_comments = Comment.objects.all_parent_comments().count()
        self.assertEqual(all_comments, 0)
        self.assertEqual(parent_comments, 0)
        # parent comment
        data = {
            'content': 'parent comment body',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id,
            'is_parent': True
        }
        response = self.client.post(reverse('comment:create'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_parent'])
        self.assertIsNone(response.context.get('reply'))
        self.assertTemplateUsed(response, 'comment/base.html')
        parent_comment = Comment.objects.get(content='parent comment body', object_id=self.post_1.id)
        self.assertEqual(response.context.get('comment').id, parent_comment.id)
        self.assertEqual(Comment.objects.all_parent_comments().count(), parent_comments + 1)
        self.assertEqual(Comment.objects.all().count(), all_comments + 1)

        # create child comment
        data = {
            'content': 'child comment body',
            'app_name': 'post',
            'model_name': 'post',
            'parent_id': parent_comment.id,
            'model_id': self.post_1.id,
            'is_parent': False
        }
        response = self.client.post(reverse('comment:create'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_parent'])
        self.assertIsNone(response.context.get('comment'))
        self.assertTemplateUsed(response, 'comment/child_comment.html')
        child_comment = Comment.objects.get(content='child comment body', object_id=self.post_1.id)
        self.assertEqual(response.context.get('reply').id, child_comment.id)
        self.assertEqual(Comment.objects.all_parent_comments().count(), parent_comments + 1)
        self.assertEqual(Comment.objects.all().count(), all_comments + 2)

        # create child comment with wrong content type => parent comment
        data = {
            'content': 'not child comment body',
            'app_name': 'post',
            'model_name': 'post',
            'parent_id': 100,
            'model_id': self.post_1.id,
            'is_parent': False
        }
        response = self.client.post(reverse('comment:create'), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_parent'])
        child_comment = Comment.objects.get(content='not child comment body', object_id=self.post_1.id)
        self.assertIsNone(child_comment.parent)

    def test_edit_comment(self):
        comment = self.create_comment(self.content_object_1)
        self.assertEqual(Comment.objects.all().count(), 1)
        data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id
        }
        self.assertEqual(comment.content, 'comment 1')
        response = self.client.get(reverse('comment:edit', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('comment/update_comment.html')
        self.assertEqual(response.context['comment_form'].instance.id, comment.id)

        response = self.client.post(reverse('comment:edit', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('comment/content.html')
        self.assertEqual(Comment.objects.all().first().content, data['content'])

        data['content'] = ''
        with self.assertRaises(ValueError) as error:
            self.client.post(reverse('comment:edit', kwargs={'pk': comment.id}), data=data)
        self.assertIsInstance(error.exception, ValueError)

    def test_cannot_edit_comment_by_different_user(self):
        comment = self.create_comment(self.content_object_1)
        self.client.logout()
        self.client.login(username='test-2', password='1234')
        data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id
        }
        self.assertEqual(comment.content, 'comment 1')
        self.assertEqual(comment.user.username, self.user_1.username)
        response = self.client.get(reverse('comment:edit', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, 'Forbidden')

        response = self.client.post(reverse('comment:edit', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, 'Forbidden')

    def test_delete_comment(self):
        comment = self.create_comment(self.content_object_1)
        data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id,
        }
        init_comments = Comment.objects.all().count()
        self.assertEqual(init_comments, 1)
        response = self.client.get(reverse('comment:delete', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/comment_modal.html')
        self.assertContains(response, 'html_form')

        response = self.client.post(reverse('comment:delete', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/base.html')
        self.assertNotContains(response, 'html_form')
        self.assertEqual(Comment.objects.all().count(), init_comments-1)

    def test_cannot_delete_comment_by_different_user(self):
        comment = self.create_comment(self.content_object_1)
        self.client.logout()
        self.client.login(username='test-2', password='1234')
        self.assertEqual(comment.content, 'comment 1')
        self.assertEqual(comment.user.username, self.user_1.username)
        data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id,
        }
        init_comments = Comment.objects.all().count()
        self.assertEqual(init_comments, 1)
        response = self.client.get(reverse('comment:delete', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, 'Forbidden')

        response = self.client.post(reverse('comment:delete', kwargs={'pk': comment.id}), data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, 'Forbidden')
