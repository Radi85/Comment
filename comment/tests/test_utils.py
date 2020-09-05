from unittest import TestCase
from unittest.mock import patch

from django.utils import timezone
from django.core import signing, mail
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import reverse

from comment.conf import settings
from comment.utils import (
    get_model_obj, has_valid_profile, get_comment_context_data, id_generator, get_comment_from_key,
    get_user_for_request, send_email_confirmation_request, process_anonymous_commenting, CommentFailReason,
    get_response_for_bad_request, get_data_for_request)
from comment.tests.base import BaseCommentUtilsTest, Comment, RequestFactory


class CommentUtilsTest(BaseCommentUtilsTest):
    def test_get_model_object(self):
        data = {
            'app_name': 'post',
            'model_name': 'Post',
            'model_id': self.post_1.id
        }
        model_object = get_model_obj(**data)
        self.assertIsNotNone(model_object)
        self.assertIsInstance(model_object, self.post_1.__class__)

    def test_has_valid_profile(self):
        setattr(settings, 'PROFILE_APP_NAME', 'user_profile')
        setattr(settings, 'PROFILE_MODEL_NAME', 'userprofile')
        has_profile = has_valid_profile()
        self.assertTrue(has_profile)

        # one of settings attribute is missing
        setattr(settings, 'PROFILE_MODEL_NAME', '')
        has_profile = has_valid_profile()
        self.assertFalse(has_profile)

        # settings attr provided with wrong value
        setattr(settings, 'PROFILE_MODEL_NAME', 'wrong_value')
        has_profile = has_valid_profile()
        self.assertFalse(has_profile)

        # settings attr provided, profile model has no image
        setattr(settings, 'PROFILE_MODEL_NAME', 'userprofile')
        mocked_hasattr = patch('comment.utils.hasattr').start()
        mocked_hasattr.return_value = False
        has_profile = has_valid_profile()
        self.assertFalse(has_profile)

    def test_get_comment_context_data(self):
        comment_per_page = 'COMMENT_PER_PAGE'
        login_url = 'LOGIN_URL'
        current_login_url = getattr(settings, login_url, '/profile/login/')
        comment_allow_anonymous = 'COMMENT_ALLOW_ANONYMOUS'
        oauth = 'oauth'

        init_comment_per_page = getattr(settings, comment_per_page)
        setattr(settings, login_url, current_login_url)
        setattr(settings, comment_allow_anonymous, False)
        setattr(settings, comment_per_page, 0)
        data = {
            'model_object': self.post_1,
            'model_name': 'post',
            'model_id': self.post_1.id,
            'app_name': 'post',
            'user': self.post_1.author,
            'page': 10,
            oauth: 'True'
        }
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        if current_login_url.startswith('/'):
            setattr(settings, login_url, current_login_url[1:])
        comment_context_data = get_comment_context_data(request)

        self.assertEqual(comment_context_data['comments'].count(), self.increment)
        # test inserting '/' to the beginning of login url
        self.assertEqual(comment_context_data['login_url'], '/' + settings.LOGIN_URL)
        self.assertEqual(comment_context_data['is_anonymous_allowed'], settings.COMMENT_ALLOW_ANONYMOUS)
        self.assertEqual(comment_context_data['oauth'], True)

        setattr(settings, login_url, current_login_url)
        setattr(settings, comment_per_page, 2)
        setattr(settings, comment_allow_anonymous, True)
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        comment_context_data = get_comment_context_data(request)

        self.assertEqual(comment_context_data['comments'].paginator.per_page, 2)
        self.assertTrue(comment_context_data['comments'].has_previous())
        self.assertEqual(comment_context_data['login_url'], settings.LOGIN_URL)
        self.assertEqual(comment_context_data['is_anonymous_allowed'], settings.COMMENT_ALLOW_ANONYMOUS)

        data.update({'page': 'not integer', oauth: 'False'})
        request = self.factory.post('/', data=data)
        request.user = self.post_1.author
        comment_context_data = get_comment_context_data(request)

        self.assertEqual(comment_context_data['comments'].paginator.per_page, 2)
        self.assertTrue(comment_context_data['comments'].has_next())
        self.assertEqual(comment_context_data[oauth], False)

        setattr(settings, comment_allow_anonymous, False)
        # set back to the default value
        setattr(settings, comment_per_page, init_comment_per_page)

    def test_user_for_request(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()
        # test unauthenticated user
        self.assertIsNone(get_user_for_request(request))
        # test authenticated user
        request.user = self.user_1
        self.assertEqual(get_user_for_request(request), self.user_1)


class BaseAnonymousCommentTest(BaseCommentUtilsTest):
    def setUp(self):
        super().setUp()
        self.time_posted = timezone.now()
        _email = 'test-1@acme.edu'
        _content = 'posting anonymous comment'
        _parent = None
        _factory = RequestFactory()
        self.comment_obj = Comment(
            content_object=self.post_1,
            content=_content,
            user=None,
            parent=_parent,
            email=_email,
            posted=self.time_posted
        )

        self.key = signing.dumps(self.comment_obj.to_dict(), compress=True)
        self.request = _factory.get('/')
        self.site = get_current_site(self.request)


class TestGetCommentFromKey(BaseAnonymousCommentTest, BaseCommentUtilsTest):
    def test_bad_signature(self):
        key = self.key + 'invalid'
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_key_error(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment_dict.pop('model_name')
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_attribute_error(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment_dict['model_name'] = 1
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_value_error(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment_dict['user'] = 1
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.BAD)
        self.assertIsNone(response.obj)

    def test_comment_exists(self):
        comment_dict = self.comment_obj.to_dict().copy()
        comment = self.create_anonymous_comment(posted=timezone.now(), email='a@a.com')
        comment_dict.update({
            'posted': str(comment.posted),
            'email': comment.email
        })
        key = signing.dumps(comment_dict)
        response = get_comment_from_key(key)

        self.assertEqual(response.is_valid, False)
        self.assertEqual(response.why_invalid, CommentFailReason.EXISTS)
        self.assertIsNone(response.obj)

    def test_success(self):
        response = get_comment_from_key(self.key)

        self.assertEqual(response.is_valid, True)
        self.assertEqual(response.why_invalid, None)
        self.assertIsInstance(response.obj, Comment)
        # comment is saved
        self.assertIsNotNone(response.obj.id)
        self.assertEqual(response.obj.posted, self.time_posted)


@patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
class TestSendEmailConfirmationRequest(BaseAnonymousCommentTest, BaseCommentUtilsTest):
    def setUp(self):
        super().setUp()
        settings.COMMENT_CONTACT_EMAIL = 'contact@domain'
        settings.COMMENT_FROM_EMAIL = 'no-reply@domain'
        self.len_mailbox = len(mail.outbox)
        self.confirmation_url = reverse('comment:confirm-comment', args=[self.key])
        self.confirmation_url_drf = f'/api/comments/confirm/{self.key}/'
        self.contact_email = settings.COMMENT_CONTACT_EMAIL
        self.receivers = [self.comment_obj.to_dict()['email']]
        self.sender = settings.COMMENT_FROM_EMAIL
        self.subject = 'Comment Confirmation Request'
        self.content_object_url = f'http://{self.site.domain}{self.comment_obj.content_object.get_absolute_url()}'

    def email_contents_test(self, contents, api=False):
        if not api:
            confirmation_url = self.confirmation_url
        else:
            confirmation_url = self.confirmation_url_drf

        # message context contains comment content, confirmation url, contact email, site name,\
        # content object's absolute url.
        self.assertEqual(True, self.comment_obj.content in contents)
        self.assertEqual(True, confirmation_url in contents)
        self.assertEqual(True, self.contact_email in contents)
        self.assertEqual(True, self.site.name in contents)
        self.assertEqual(True, self.content_object_url in contents)

    def email_metadata_test(self, email, html=False):
        self.assertEqual(email.from_email, self.sender)
        self.assertEqual(email.to, self.receivers)
        self.assertEqual(email.subject, self.subject)
        if html:
            self.assertEqual(email.alternatives[0][1], 'text/html')
        else:
            self.assertEqual(email.alternatives, [])

    @patch.object(settings, 'COMMENT_SEND_HTML_EMAIL', False)
    def test_sending_only_text_template_with_django(self):
        receiver = self.comment_obj.to_dict()['email']
        len_mailbox = self.len_mailbox
        response = send_email_confirmation_request(self.comment_obj, receiver, self.key, self.site)
        self.assertIsNone(response)
        self.assertEqual(len(mail.outbox), len_mailbox + 1)
        sent_email = mail.outbox[0]

        self.email_metadata_test(sent_email)
        self.email_contents_test(sent_email.body)

    @patch.object(settings, 'COMMENT_SEND_HTML_EMAIL', False)
    def test_sending_only_text_template_with_drf(self):
        receiver = self.comment_obj.to_dict()['email']
        len_mailbox = self.len_mailbox
        response = send_email_confirmation_request(self.comment_obj, receiver, self.key, self.site, api=True)
        self.assertIsNone(response)
        self.assertEqual(len(mail.outbox), len_mailbox + 1)
        sent_email = mail.outbox[0]

        self.email_metadata_test(sent_email)
        self.email_contents_test(sent_email.body, api=True)

    @patch.object(settings, 'COMMENT_SEND_HTML_EMAIL', True)
    def test_sending_both_text_and_html_template_with_django(self):
        receiver = self.comment_obj.to_dict()['email']
        len_mailbox = self.len_mailbox
        response = send_email_confirmation_request(self.comment_obj, receiver, self.key, self.site)
        self.assertIsNone(response)
        self.assertEqual(len(mail.outbox), len_mailbox + 1)
        sent_email = mail.outbox[0]

        self.email_metadata_test(sent_email, html=True)
        self.email_contents_test(sent_email.body)

    @patch.object(settings, 'COMMENT_SEND_HTML_EMAIL', True)
    def test_sending_both_text_and_html_template_with_drf(self):
        receiver = self.comment_obj.to_dict()['email']
        len_mailbox = self.len_mailbox
        response = send_email_confirmation_request(self.comment_obj, receiver, self.key, self.site, api=True)
        self.assertIsNone(response)
        self.assertEqual(len(mail.outbox), len_mailbox + 1)
        sent_email = mail.outbox[0]

        self.email_metadata_test(sent_email, html=True)
        self.email_contents_test(sent_email.body, api=True)


class TestProcessAnonymousCommenting(BaseAnonymousCommentTest, BaseCommentUtilsTest):
    def setUp(self):
        super().setUp()
        self.request.user = AnonymousUser()
        self.response_msg = (
            'We have have sent a verification link to your email. The comment will be '
            'displayed after it is verified.'
        )

    def test_for_django(self):
        response = process_anonymous_commenting(self.request, self.comment_obj)
        self.assertEqual(self.response_msg, response)

    def test_for_drf(self):
        response = process_anonymous_commenting(self.request, self.comment_obj, api=True)
        self.assertEqual(self.response_msg, response)


class TestGetResponseForBadRequest(BaseCommentUtilsTest):

    def test_for_django(self):
        why = 'failed'
        response = get_response_for_bad_request(why=why)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), why)

    def test_for_drf(self):
        why = 'failed'
        response = get_response_for_bad_request(why=why, api=True)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], why)


class TestGetDataForRequest(BaseCommentUtilsTest):
    """For django, POST requests are allowed. For DRF, GET requests are allowed"""
    def test_for_django(self):
        key = 'key'
        val = 'val'
        request = self.factory.post('/', data={key: val})
        response = get_data_for_request(request)

        self.assertEqual(response.get('key'), val)

    def test_for_drf(self):
        key = 'key'
        val = 'val'
        request = self.factory.get('/', data={key: val})
        response = get_data_for_request(request, api=True)

        self.assertEqual(response.get('key'), val)


class UtilsTest(TestCase):
    """Test general purpose utilities that aren't necessarily related to a comment"""

    def setUp(self):
        self.len_id = 6

    def test_id_generator_length(self):
        self.assertEqual(self.len_id, len(id_generator()))

    def test_id_generator_generates_different_ids(self):
        self.assertNotEqual(id_generator(), id_generator())

    def test_id_generator_prefix(self):
        prefix = 'comment'
        output = id_generator(prefix=prefix)
        self.assertEqual(True, output.startswith(prefix))
        self.assertEqual(self.len_id + len(prefix), len(output))

    def test_id_generator_suffix(self):
        suffix = 'comment'
        output = id_generator(suffix=suffix)
        self.assertEqual(True, output.endswith(suffix))
        self.assertEqual(self.len_id + len(suffix), len(output))

    def test_id_generator_chars(self):
        import string   # flake8:no qa
        chars = string.ascii_uppercase
        output = id_generator(chars=chars)
        self.assertEqual(output, output.upper())

    def test_id_generator_len(self):
        len_id = 8
        self.assertEqual(len_id, len(id_generator(len_id=len_id)))
