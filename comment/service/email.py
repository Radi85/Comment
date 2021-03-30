from threading import Thread

from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import loader
from django.urls import reverse

from comment.conf import settings
from comment.messages import EmailInfo
from comment.models import Follower


class DABEmailService(object):
    def __init__(self, comment, request):
        self.comment = comment
        self.request = request
        self.sender = settings.COMMENT_FROM_EMAIL
        self.is_html = settings.COMMENT_SEND_HTML_EMAIL
        self._email_thread = None

    def get_msg_context(self, **context):
        context['comment'] = self.comment
        context['site'] = get_current_site(self.request)
        context['contact'] = settings.COMMENT_CONTACT_EMAIL
        return context

    def get_message(self, subject, body, receivers, html_msg=None):
        msg = EmailMultiAlternatives(subject, body, self.sender, receivers)
        if html_msg:
            msg.attach_alternative(html_msg, 'text/html')
        return msg

    def send_messages(self, messages):
        connection = get_connection()  # Use default email connection
        self._email_thread = Thread(target=connection.send_messages, args=(messages,))
        self._email_thread.start()

    def get_message_templates(self, text_template, html_template, msg_context):
        text_msg_template = loader.get_template(text_template)
        text_msg = text_msg_template.render(msg_context)
        html_msg = None
        if self.is_html:
            html_msg_template = loader.get_template(html_template)
            html_msg = html_msg_template.render(msg_context)
        return text_msg, html_msg

    def send_confirmation_request(self, api=False):
        comment_dict = self.comment.to_dict()
        receivers = [comment_dict['email']]
        key = signing.dumps(comment_dict, compress=True)
        text_template = 'comment/anonymous/confirmation_request.txt'
        html_template = 'comment/anonymous/confirmation_request.html'
        subject = EmailInfo.CONFIRMATION_SUBJECT
        if api:
            confirmation_url = reverse('comment-api:confirm-comment', args=[key])
        else:
            confirmation_url = reverse('comment:confirm-comment', args=[key])

        context = self.get_msg_context(confirmation_url=confirmation_url)
        text_msg, html_msg = self.get_message_templates(text_template, html_template, context)
        msg = self.get_message(subject, text_msg, receivers, html_msg=html_msg)
        self.send_messages([msg])

    def get_thread(self):
        if self.comment.is_parent:
            return self.comment.content_object
        return self.comment.parent

    def get_thread_name(self):
        if self.comment.is_parent:
            return str(self.comment.content_object)
        return str(self.comment.parent).split(':')[0]

    def get_subject_for_notification(self, thread_name):
        username = self.comment.get_username()
        return EmailInfo.NOTIFICATION_SUBJECT.format(username=username, thread_name=thread_name)

    def get_messages_for_notification(self, thread_name, receivers):
        text_template = 'comment/notifications/notification.txt'
        html_template = 'comment/notifications/notification.html'
        subject = self.get_subject_for_notification(thread_name)
        messages = []
        for receiver in receivers:
            context = self.get_msg_context(thread_name=thread_name, receiver=receiver.username)
            text_msg, html_msg = self.get_message_templates(text_template, html_template, context)
            messages.append(self.get_message(subject, text_msg, [receiver.email], html_msg=html_msg))
        return messages

    def send_notification_to_followers(self):
        thread = self.get_thread()
        followers = Follower.objects.filter_for_model_object(thread).exclude(email=self.comment.email)
        if not followers:
            return
        thread_name = self.get_thread_name()
        messages = self.get_messages_for_notification(thread_name, followers)
        self.send_messages(messages)
