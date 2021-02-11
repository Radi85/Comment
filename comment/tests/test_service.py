from unittest.mock import patch

from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import reverse

from comment.conf import settings
from comment.tests.test_utils import BaseAnonymousCommentTest
from comment.service.email import DABEmailService
from comment.messages import EmailInfo
from comment.models import Follower


@patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
@patch.object(settings, 'COMMENT_FROM_EMAIL', 'no-reply@domain')
@patch.object(settings, 'COMMENT_CONTACT_EMAIL', 'contact@domain')
class TestDABEmailService(BaseAnonymousCommentTest):
    def setUp(self):
        super().setUp()
        self.email_service = DABEmailService(self.comment_obj, self.request)
        self.confirmation_url = reverse('comment:confirm-comment', args=[self.key])
        self.confirmation_url_drf = f'/api/comments/confirm/{self.key}/'
        self.contact_email = settings.COMMENT_CONTACT_EMAIL
        self.receivers = []
        self.sender = settings.COMMENT_FROM_EMAIL
        self.site = self.email_service.get_msg_context()['site']
        self.content_object_url = f'http://{self.site.domain}{self.comment_obj.content_object.get_absolute_url()}'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.child_comment = cls.create_comment(cls.content_object_1, parent=cls.comment_1)

    def email_contents_test(self, contents, *args):
        for arg in args:
            self.assertTrue(arg in contents)
        self.assertTrue(self.site.name in contents)
        self.assertTrue(self.content_object_url in contents)

    def email_metadata_test(self, email):
        self.assertEqual(email.from_email, self.sender)
        self.assertEqual(email.to, self.receivers)
        if self.email_service.is_html:
            self.assertEqual(email.alternatives[0][1], 'text/html')
        else:
            self.assertEqual(email.alternatives, [])

    def test_can_create_service(self):
        self.assertIsNotNone(self.email_service)

    def test_get_msg_context(self):
        context = self.email_service.get_msg_context(test='test')
        self.assertEqual(context['comment'], self.comment_obj)
        self.assertEqual(context['contact'], settings.COMMENT_CONTACT_EMAIL)
        self.assertEqual(context['test'], 'test')
        self.assertIn('site', context.keys())

    def test_get_message_for_txt(self):
        subject = 'test subject'
        body = 'test body'
        msg = self.email_service.get_message(subject, body, self.receivers)
        self.assertIsInstance(msg, EmailMultiAlternatives)
        self.assertEqual(msg.to, self.receivers)
        self.assertEqual(msg.alternatives, [])

    def test_get_message_for_html(self):
        subject = 'test subject'
        body = 'test body'
        html = 'html_test'
        msg = self.email_service.get_message(subject, body, self.receivers, html_msg=html)
        self.assertIsInstance(msg, EmailMultiAlternatives)
        self.assertEqual(msg.to, self.receivers)
        self.assertEqual(msg.alternatives, [(html, 'text/html')])

    @patch.object(settings, 'COMMENT_SEND_HTML_EMAIL', False)
    def test_get_message_templates_text_only(self):
        email_service = DABEmailService(self.comment_obj, self.request)
        context = self.email_service.get_msg_context()
        text_template = 'comment/anonymous/confirmation_request.txt'
        html_template = 'comment/anonymous/confirmation_request.html'
        text_msg, html_msg = email_service.get_message_templates(text_template, html_template, context)
        self.assertFalse(email_service.is_html)
        self.assertIsNotNone(text_msg)
        self.assertIsNone(html_msg)

    def test_get_message_templates_with_html(self):
        context = self.email_service.get_msg_context()
        text_template = 'comment/anonymous/confirmation_request.txt'
        html_template = 'comment/anonymous/confirmation_request.html'
        text_msg, html_msg = self.email_service.get_message_templates(text_template, html_template, context)
        self.assertTrue(self.email_service.is_html)
        self.assertIsNotNone(text_msg)
        self.assertIsNotNone(html_msg)

    def test_send_messages(self):
        self.receivers = ['test@test']
        messages = [
            self.email_service.get_message('test subject', 'test body', ['test@test'], html_msg='test msg')
            for _ in range(100)
        ]
        self.assertEqual(len(mail.outbox), 0)
        self.email_service.send_messages(messages)
        self.assertNotEqual(len(mail.outbox), 100)
        self.assertTrue(self.email_service._email_thread.is_alive())
        self.email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 100)

    def test_send_confirmation_request_django(self):
        self.email_service.send_confirmation_request()
        self.email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIsInstance(sent_email, EmailMultiAlternatives)
        self.assertEqual(sent_email.subject, EmailInfo.CONFIRMATION_SUBJECT)
        self.email_contents_test(
            sent_email.body, self.confirmation_url, self.comment_obj.content, self.contact_email
        )
        self.receivers = [self.comment_obj.to_dict()['email']]
        self.email_metadata_test(sent_email)

    def test_send_confirmation_request_api(self):
        self.email_service.send_confirmation_request(api=True)
        self.email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIsInstance(sent_email, EmailMultiAlternatives)
        self.email_contents_test(
            sent_email.body, self.confirmation_url_drf, self.comment_obj.content, self.contact_email
        )
        self.assertEqual(sent_email.subject, EmailInfo.CONFIRMATION_SUBJECT)
        self.receivers = [self.comment_obj.to_dict()['email']]
        self.email_metadata_test(sent_email)

    def test_get_thread_for_parent_comment(self):
        """The content type (Post, Picture...) is the parent thread of a parent comment"""
        self.assertTrue(self.email_service.comment.is_parent)
        thread = self.email_service.get_thread()
        self.assertIs(thread, self.email_service.comment.content_object)
        self.assertIsInstance(thread, self.email_service.comment.content_object.__class__)

    def test_get_thread_for_child_comment(self):
        """The parent comment is the parent thread of a child comment"""
        self.assertFalse(self.child_comment.is_parent)
        email_service = DABEmailService(self.child_comment, self.request)
        self.assertFalse(email_service.comment.is_parent)
        thread = email_service.get_thread()
        self.assertIsNot(thread, email_service.comment.content_object)
        self.assertIs(thread, email_service.comment.parent)

    def test_get_thread_name_for_parent_comment(self):
        self.assertTrue(self.email_service.comment.is_parent)
        thread_name = self.email_service.get_thread_name()
        self.assertEqual(thread_name, str(self.email_service.comment.content_object))

    def test_get_thread_name_for_child_comment(self):
        email_service = DABEmailService(self.child_comment, self.request)
        self.assertFalse(email_service.comment.is_parent)
        thread_name = email_service.get_thread_name()
        self.assertEqual(thread_name, str(email_service.comment.parent).split(':')[0])

    def test_send_notification_to_followers_return_none(self):
        """return None if the thread has no followers"""
        followers = Follower.objects.filter_for_model_object(
            self.comment_obj.content_object).exclude(email=self.comment_obj.email)
        self.assertEqual(followers.count(), 0)
        result = self.email_service.send_notification_to_followers()
        self.assertIsNone(result)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_notification_to_followers(self):
        Follower.objects.follow('any@test.com', 'test_user', self.comment_obj.content_object)
        followers = Follower.objects.filter_for_model_object(
            self.comment_obj.content_object).exclude(email=self.comment_obj.email)
        self.assertEqual(followers.count(), 1)

        self.email_service.send_notification_to_followers()
        self.email_service._email_thread.join()

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIsInstance(sent_email, EmailMultiAlternatives)
        username = self.comment_obj.get_username()
        thread_name = str(self.comment_obj.content_object)
        self.email_contents_test(sent_email.body, username, self.comment_obj.content)
        self.assertEqual(
            sent_email.subject,
            EmailInfo.NOTIFICATION_SUBJECT.format(username=username, thread_name=thread_name)
        )
        self.receivers = [followers.first().email]
        self.email_metadata_test(sent_email)
