from django.urls import reverse
from rest_framework import status

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
            'model_id': self.post_1.id
        }
        response = self.client.post(reverse('comment:create'), data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/base.html')
        parent_comment = Comment.objects.get(content='parent comment body', object_id=self.post_1.id)
        self.assertEqual(response.context.get('comment').id, parent_comment.id)
        self.assertTrue(response.context.get('comment').is_parent)
        self.assertEqual(Comment.objects.all_parent_comments().count(), parent_comments + 1)
        self.assertEqual(Comment.objects.all().count(), all_comments + 1)

        # create child comment
        data = {
            'content': 'child comment body',
            'app_name': 'post',
            'model_name': 'post',
            'parent_id': parent_comment.id,
            'model_id': self.post_1.id
        }
        response = self.client.post(reverse('comment:create'), data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/child_comment.html')
        child_comment = Comment.objects.get(content='child comment body', object_id=self.post_1.id)
        self.assertEqual(response.context.get('comment').id, child_comment.id)
        self.assertFalse(response.context.get('comment').is_parent)
        self.assertEqual(Comment.objects.all_parent_comments().count(), parent_comments + 1)
        self.assertEqual(Comment.objects.all().count(), all_comments + 2)

        # create child comment with wrong content type => parent comment
        data = {
            'content': 'not child comment body',
            'app_name': 'post',
            'model_name': 'post',
            'parent_id': 100,
            'model_id': self.post_1.id
        }
        response = self.client.post(reverse('comment:create'), data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        child_comment = Comment.objects.get(content='not child comment body', object_id=self.post_1.id)
        self.assertTrue(child_comment.is_parent)
        self.assertIsNone(child_comment.parent)

    def test_create_comment_non_ajax_request(self):
        data = {
            'content': 'parent comment body',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id
        }
        response = self.client.post(reverse('comment:create'), data=data)
        self.assertEqual(response.status_code, 400)  # bad request

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


class SetReactionTest(BaseCommentTest):

    def setUp(self):
        super().setUp()
        self.comment = self.create_comment(self.content_object_1)

    def get_url(self, obj_id, action):
        """
        A utility function to construct url.

        Args:
            obj_id (int): comment id
            action (str): reaction(like/dislike)

        Returns:
            str
        """
        return reverse('comment:react', kwargs={
            'pk': obj_id,
            'reaction': action
        })

    def request(self, url, method='post', is_ajax=True):
        """
        A utility function to return perform client requests.
        Args:
            url (str): The url to perform that needs to be requested.
            method (str, optional): The HTTP method name. Defaults to 'POST'.
            is_ajax (bool, optional): Whether AJAX request is to be performed or not. Defaults to True.

        Raises:
            ValueError: When a invalid HTTP method name is passed.

        Returns:
            `Any`: Response from the request.
        """
        request_method = getattr(self.client, method.lower(), None)
        if not request_method:
            raise ValueError('This is not a valid request method')
        if is_ajax:
            return request_method(url, **{
                'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'
            })
        return request_method(url)

    def test_set_reaction_for_authenticated_users(self):
        """Test whether users can create/change reactions using view"""
        url = self.get_url(self.comment.id, 'like')
        response = self.request(url)
        data = {
            'status': 0,
            'likes': 1,
            'dislikes': 0,
            'msg': 'Your reaction has been updated successfully'
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), data)

    def test_set_reaction_for_unauthenticated_users(self):
        """Test whether unauthenticated users can create/change reactions using view"""
        url = self.get_url(self.comment.id, 'dislike')
        self.client.logout()
        response = self.request(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/login?next={}'.format(url))

    def test_get_request(self):
        """Test whether GET requests are allowed or not"""
        url = self.get_url(self.comment.id, 'like')
        response = self.request(url, method='get')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_non_ajax_requests(self):
        """Test response if non AJAX requests are sent"""
        url = self.get_url(self.comment.id, 'like')
        response = self.request(url, is_ajax=False)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_incorrect_comment_id(self):
        """Test response when an incorrect comment id is passed"""
        url = self.get_url(102_876, 'like')
        response = self.request(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_incorrect_reaction(self):
        """Test response when incorrect reaction is passed"""
        url = self.get_url(self.comment.id, 'likes')
        response = self.request(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test incorrect type
        url = self.get_url(self.comment.id, 1)
        response = self.request(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
