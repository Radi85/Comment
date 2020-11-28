import sys
from unittest.mock import patch

from rest_framework import status

from comment.exceptions import CommentBadRequest
from comment.tests.base import TestCase
from comment.messages import ExceptionError


class CommentExceptionTest(TestCase):
    _default_detail = ExceptionError.BAD_REQUEST

    def test_can_create_custom_error_without_params(self):
        exception = CommentBadRequest()

        self.assertEqual(exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exception.detail, self._default_detail)

    def test_create_custom_error_with_params(self):
        detail = 'not found'
        exception = CommentBadRequest(detail=detail, status_code=404)

        self.assertEqual(exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exception.detail, detail)

    def test_create_custom_error_without_drf_installed(self):
        with patch.dict(sys.modules, {'rest_framework.exceptions': None}):
            from importlib import reload
            reload(sys.modules['comment.exceptions'])
            from comment.exceptions import CommentBadRequest
            exception = CommentBadRequest()

        self.assertEqual(exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exception.detail, self._default_detail)
