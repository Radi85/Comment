from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils import timezone
from django.core import signing, mail
from django.urls import reverse
from rest_framework import status
from django.contrib import messages

from comment.conf import settings
from comment.models import Comment, Follower
from comment.messages import EmailInfo, EmailError
from comment.tests.base import BaseCommentViewTest
from comment.tests.test_utils import BaseAnonymousCommentTest
from comment.views import ConfirmComment


class CommentViewTestCase(BaseCommentViewTest):
    def setUp(self):
        super().setUp()
        self.all_comments = Comment.objects.all().count()
        self.parent_comments = Comment.objects.all_parents().count()
        self.data = {
            'content': 'comment body',
            'app_name': 'post',
            'model_name': 'post',
            'parent_id': '',
            'model_id': self.post_1.id
        }

    def increase_count(self, parent=False):
        if parent:
            self.parent_comments += 1

        self.all_comments += 1

    @staticmethod
    def get_create_url():
        return reverse('comment:create')

    def comment_count_test(self):
        self.assertEqual(Comment.objects.all_parents().count(), self.parent_comments)
        self.assertEqual(Comment.objects.all().count(), self.all_comments)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_create_parent_comment(self):
        self.assertEqual(self.all_comments, 0)
        self.assertEqual(self.parent_comments, 0)

        url = self.get_create_url()
        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/comments/base.html')

        parent_comment = Comment.objects.get(object_id=self.post_1.id, parent=None)

        self.assertEqual(response.context.get('comment').id, parent_comment.id)
        self.assertTrue(response.context.get('comment').is_parent)

        self.increase_count(parent=True)
        self.comment_count_test()

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_create_child_comment(self):
        self.assertEqual(self.all_comments, 0)
        self.assertEqual(self.parent_comments, 0)

        url = self.get_create_url()
        data = self.data.copy()
        parent_comment = self.create_comment(self.post_1)
        self.increase_count(parent=True)
        self.comment_count_test()
        data['parent_id'] = parent_comment.id
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/comments/child_comment.html')

        child_comment = Comment.objects.get(object_id=self.post_1.id, parent=parent_comment)
        self.assertEqual(response.context.get('comment').id, child_comment.id)
        self.assertFalse(response.context.get('comment').is_parent)

        self.increase_count()
        self.comment_count_test()

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_send_notification_to_thread_followers_on_create_comment(self):
        Follower.objects.follow('te@te.com', 'test_user', self.post_1)
        self.assertEqual(len(mail.outbox), 0)
        url = self.get_create_url()
        response = self.client.post(url, data=self.data)

        self.assertEqual(response.status_code, 200)
        response.context['view'].email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 1)

    def test_create_comment_non_ajax_request(self):
        response = self.client_non_ajax.post(self.get_create_url(), data=self.data)

        self.assertEqual(response.status_code, 403)

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_anonymous_comment(self):
        self.client.logout()
        data = self.data.copy()
        data['email'] = 'a@a.com'
        url = self.get_create_url()
        self.assertEqual(len(mail.outbox), 0)

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'comment/comments/base.html')
        self.assertEqual(response.json()['msg'], EmailInfo.CONFIRMATION_SENT)
        # confirmation email is sent
        response.context['view'].email_service._email_thread.join()

        self.assertEqual(len(mail.outbox), 1)

        # no change in comment count
        self.comment_count_test()

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_anonymous_comment_with_invalid_email(self):
        self.client.logout()
        data = self.data.copy()
        data['email'] = 'test@invalid.c'
        url = self.get_create_url()

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], EmailError.EMAIL_INVALID)


class TestEditComment(BaseCommentViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_comment(cls.content_object_1)
        cls.init_content = cls.comment.content

    def test_edit_comment(self):
        comment = self.create_comment(self.content_object_1)
        self.client.force_login(comment.user)
        self.assertEqual(Comment.objects.all().count(), 2)
        data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id
        }
        get_url = self.get_url('comment:edit', comment.id, data)
        self.assertEqual(comment.content, 'comment 2')
        response = self.client.get(get_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('comment/comments/update_comment.html')
        self.assertHtmlTranslated(response.content, get_url)
        self.assertEqual(response.context['comment_form'].instance.id, comment.id)

        post_url = self.get_url('comment:edit', comment.id)
        response = self.client.post(post_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('comment/comments/comment_content.html')
        comment.refresh_from_db()
        self.assertEqual(comment.content, data['content'])

        data['content'] = ''
        with self.assertRaises(ValueError) as error:
            self.client.post(
                self.get_url('comment:edit', comment.id), data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
        self.assertIsInstance(error.exception, ValueError)

    def test_cannot_edit_comment_by_different_user(self):
        comment = self.comment
        self.client.force_login(self.user_2)
        data = {
            'content': 'parent comment was edited',
            'app_name': 'post',
            'model_name': 'post',
            'model_id': self.post_1.id
        }
        self.assertEqual(comment.user.username, self.user_1.username)
        response = self.client.get(self.get_url('comment:edit', comment.id), data=data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, 'Forbidden')

        response = self.client.post(self.get_url('comment:edit', comment.id), data=data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, 'Forbidden')


class TestDeleteComment(BaseCommentViewTest):

    def response_fails_test(self, response, comment):
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, 'Forbidden')
        # comment has not been deleted
        self.assertEqual(comment, Comment.objects.get(id=comment.id))

    def test_delete_comment(self):
        comment = self.create_comment(self.content_object_1)
        self.client.force_login(comment.user)
        init_count = Comment.objects.all().count()
        self.assertEqual(init_count, 1)
        get_url = self.get_url('comment:delete', comment.id, self.data)
        response = self.client.get(get_url, data=self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/comments/comment_modal.html')
        self.assertContains(response, 'data')
        self.assertHtmlTranslated(response.json()['data'], get_url)

        post_url = self.get_url('comment:delete', comment.id)
        response = self.client.post(post_url, data=self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'comment/comments/base.html')
        self.assertHtmlTranslated(response.content, post_url)
        self.assertNotContains(response, 'html_form')
        self.assertRaises(Comment.DoesNotExist, Comment.objects.get, id=comment.id)
        self.assertEqual(Comment.objects.all().count(), init_count-1)

    def test_delete_comment_by_moderator(self):
        comment = self.create_comment(self.content_object_1)
        self.client.force_login(self.moderator)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.moderator.id)
        self.assertTrue(self.moderator.has_perm('comment.delete_flagged_comment'))
        self.assertEqual(comment.user, self.user_1)
        init_count = Comment.objects.count()
        self.assertEqual(init_count, 1)
        # moderator cannot delete un-flagged comment
        response = self.client.post(self.get_url('comment:delete', comment.id), data=self.data)

        self.assertEqual(response.status_code, 403)

        # moderator can delete flagged comment
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1):
            self.create_flag_instance(self.user_1, comment)
            self.create_flag_instance(self.user_2, comment)
            response = self.client.post(self.get_url('comment:delete', comment.id), data=self.data)
            self.assertEqual(response.status_code, 200)
            self.assertRaises(Comment.DoesNotExist, Comment.objects.get, id=comment.id)

    def test_delete_comment_by_admin(self):
        comment = self.create_comment(self.content_object_1)
        self.client.force_login(self.admin)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.admin.id)
        self.assertTrue(self.admin.groups.filter(name='comment_admin').exists())
        self.assertEqual(comment.user, self.user_1)
        init_count = Comment.objects.count()
        self.assertEqual(init_count, 1)

        # admin can delete any comment
        response = self.client.post(self.get_url('comment:delete', comment.id), data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), init_count - 1)

    def test_cannot_delete_comment_by_different_user(self):
        user = self.user_2
        comment = self.create_comment(self.content_object_1)
        self.client.force_login(user)

        assert comment.user.username != user

        # test GET request
        response = self.client.get(self.get_url('comment:delete', comment.id), data=self.data)
        self.response_fails_test(response, comment)

        # test POST request
        response = self.client.post(self.get_url('comment:delete', comment.id), data=self.data)
        self.response_fails_test(response, comment)


class ConfirmCommentViewTest(BaseAnonymousCommentTest):
    def setUp(self):
        super().setUp()
        # although this will work for authenticated users as well.
        self.client.logout()
        self.request.user = AnonymousUser()
        self.init_count = Comment.objects.all().count()
        self.template_1 = 'comment/anonymous/discarded.html'
        self.template_2 = 'comment/comments/messages.html'
        self.template_3 = 'comment/bootstrap.html'

    def get_url(self, key=None):
        if not key:
            key = self.key
        return reverse('comment:confirm-comment', args=[key])

    def template_used_test(self, response):
        self.assertTemplateUsed(response, self.template_1)
        self.assertTemplateUsed(response, self.template_2)
        self.assertTemplateUsed(response, self.template_3)

    def test_bad_signature(self):
        key = self.key + 'invalid'
        _url = self.get_url(key)
        response = self.client.get(_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.all().count(), self.init_count)
        self.template_used_test(response)
        response_messages = response.context['messages']
        self.assertEqual(len(response_messages), 1)
        for r in response_messages:
            self.assertEqual(r.level, messages.ERROR)
            self.assertEqual(r.message, EmailError.BROKEN_VERIFICATION_LINK)
            self.assertTextTranslated(r.message, _url)

    def test_comment_exists(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment = self.create_anonymous_comment(posted=timezone.now(), email='a@a.com')
        init_count = self.init_count + 1
        comment_dict.update({
            'posted': str(comment.posted),
            'email': comment.email
        })
        key = signing.dumps(comment_dict)
        _url = self.get_url(key)
        response = self.client.get(_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Comment.objects.all().count(), init_count)
        self.template_used_test(response)
        self.assertHtmlTranslated(response.content, _url)
        response_messages = response.context['messages']
        self.assertEqual(len(response_messages), 1)
        for r in response_messages:
            self.assertEqual(r.level, messages.WARNING)
            self.assertEqual(r.message, EmailError.USED_VERIFICATION_LINK)
            self.assertTextTranslated(r.message, _url)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_success_without_notification(self):
        response = self.client.get(self.get_url())
        comment = Comment.objects.get(email=self.comment_obj.email, posted=self.time_posted)
        self.assertEqual(Comment.objects.all().count(), self.init_count + 1)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, comment.get_url(self.request))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_success_with_notification(self):
        self.assertEqual(len(mail.outbox), 0)
        Follower.objects.follow('t@r.com', 'test_user', self.post_1)
        request = RequestFactory().get(self.get_url())
        request.user = self.user_2
        view = ConfirmComment()
        response = view.get(request, key=self.key)
        comment = Comment.objects.get(email=self.comment_obj.email, posted=self.time_posted)

        self.assertEqual(Comment.objects.all().count(), self.init_count + 1)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, comment.get_url(self.request))

        view.email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 1)
