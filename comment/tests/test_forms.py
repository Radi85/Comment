from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser

from comment.forms import CommentForm
from comment.tests.base import BaseCommentTest, RequestFactory
from comment.conf import settings
from comment.messages import EmailInfo


class TestCommentForm(BaseCommentTest):
    def setUp(self):
        super().setUp()
        factory = RequestFactory()
        self.request = factory.get('/')

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_create_comment_form(self):
        self.request.user = self.user_1
        form = CommentForm(request=self.request)

        self.assertIsNone(form.fields.get('email', None))

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_anonymous_comment_form(self):
        self.request.user = AnonymousUser()
        form = CommentForm(request=self.request)
        field = 'email'
        email_field = form.fields.get(field, None)

        self.assertIsNotNone(email_field)
        self.assertEqual(email_field.label, EmailInfo.LABEL)
        self.assertTextTranslated(email_field.label)
        self.assertEqual(email_field.widget.input_type, field)
        self.assertDictEqual(email_field.widget.attrs, {
            'placeholder': EmailInfo.INPUT_PLACEHOLDER,
            'title': EmailInfo.INPUT_TITLE
        })

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_anonymous_comment_without_email(self):
        self.request.user = AnonymousUser()
        field = 'email'
        email = 'A@a.com '
        form = CommentForm(request=self.request, data={field: email})

        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.clean_email(), email.lower().strip())
