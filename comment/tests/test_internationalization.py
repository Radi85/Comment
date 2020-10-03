from django.shortcuts import render
from django.template.loader import render_to_string
from django.test import RequestFactory

from comment.tests.base import BaseCommentTest


class InternationalizationTest(BaseCommentTest):
    """Testing values are not necessarily returned from a view functions"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        comment = cls.create_comment(cls.content_object_1)
        cls.context = {'comment': comment}

    def setUp(self):
        super().setUp()
        factory = RequestFactory()
        self.request = factory.get('/')

    def test_confirmation_email_template_text(self):
        response = render_to_string(template_name='comment/anonymous/confirmation_request.txt', context=self.context)
        self.assertHtmlTranslated(response)

    def test_confirmation_email_template_html(self):
        response = render(
            self.request,
            template_name='comment/anonymous/confirmation_request.html',
            context=self.context
        )
        self.assertHtmlTranslated(response.content)
