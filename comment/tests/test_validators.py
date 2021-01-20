from unittest.mock import patch

from django.http import JsonResponse
from django.test import TestCase
from django.views import View
from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.generics import ListAPIView

from comment.tests.base import BaseCommentMixinTest
from comment.validators import CommentBadRequest, ValidatorMixin, _validate_order
from comment.conf import settings
from comment.messages import ExceptionError, ContentTypeError


class MockedContentTypeValidatorView(ValidatorMixin, View):
    api = False


class MockedContentTypeValidatorAPIView(ValidatorMixin, ListAPIView):
    api = True

    def get(self, request, *args, **kwargs):
        self.validate(request)
        return JsonResponse({})


class CustomValidationTest(TestCase):
    def test_can_create_custom_validation(self):
        # no params
        validator = CommentBadRequest()
        self.assertEqual(validator.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(validator.detail, ExceptionError.BAD_REQUEST)

        # with params
        validator = CommentBadRequest(detail='Not Found', status_code=404)
        self.assertEqual(validator.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(validator.detail, "Not Found")


class ValidatorMixinTest(BaseCommentMixinTest):

    def setUp(self):
        super().setUp()
        self.view = MockedContentTypeValidatorView()
        self.base_url = '/'

    def test_missing_app_name(self):
        url_data = self.data.copy()
        url_data.pop('app_name')
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.APP_NAME_MISSING)

    def test_missing_model_type(self):
        url_data = self.data.copy()
        url_data.pop('model_name')
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.MODEL_NAME_MISSING)

    def test_missing_model_id(self):
        url_data = self.data.copy()
        url_data.pop('model_id')
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.MODEL_ID_MISSING)

    def test_invalid_model_name(self):
        url_data = self.data.copy()
        model_name = 'not exists'
        url_data['model_name'] = model_name
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.MODEL_NAME_INVALID.format(model_name=model_name))

    def test_invalid_app_name(self):
        url_data = self.data.copy()
        app_name = 'not exists'
        url_data['app_name'] = app_name
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.APP_NAME_INVALID.format(app_name=app_name))

    def test_model_id_does_not_exist(self):
        url_data = self.data.copy()
        model_id = 100
        url_data['model_id'] = model_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.view.error,
            ContentTypeError.MODEL_ID_INVALID.format(model_id=model_id, model_name=url_data['model_name'])
        )

    def test_model_id_non_integral(self):
        url_data = self.data.copy()
        model_id = 'not integral'
        url_data['model_id'] = model_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.ID_NOT_INTEGER.format(var_name='model', id=model_id))

    def test_not_valid_parent_id(self):
        url_data = self.data.copy()
        parent_id = 1000
        url_data['parent_id'] = parent_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.PARENT_ID_INVALID.format(parent_id=parent_id))

    def test_parent_id_no_int(self):
        url_data = self.data.copy()
        parent_id = 'string'
        url_data['parent_id'] = parent_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, ContentTypeError.ID_NOT_INTEGER.format(var_name='parent', id=parent_id))

    def test_api_case_success(self):
        view = MockedContentTypeValidatorAPIView()
        request = self.factory.get(self.get_url(**self.data))
        response = view.dispatch(request)
        self.assertEqual(response.status_code, 200)

    def test_api_case_missing_app_name(self):
        view = MockedContentTypeValidatorAPIView()
        url_data = self.data.copy()
        url_data.pop('app_name')
        request = self.factory.get(self.get_url(**url_data))
        response = view.dispatch(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], view.error)


class ValidateOrderTest(TestCase):
    def test_success(self):
        order = ['-reaction__likes']
        with patch.object(settings, 'COMMENT_ORDER_BY', order):
            self.assertEqual(_validate_order(), order)

    def test_incorrect_value_raises_exception(self):
        order = ['err']
        with patch.object(settings, 'COMMENT_ORDER_BY', order):
            with self.assertRaises(ImproperlyConfigured) as error:
                _validate_order()

        exception = error.exception

        self.assertIsInstance(exception, ImproperlyConfigured)
        self.assertIs(order[0] in str(exception), True)

    def test_duplicate_value_raises_exception(self):
        order = ['posted', '-posted']
        with patch.object(settings, 'COMMENT_ORDER_BY', order):
            with self.assertRaises(ImproperlyConfigured) as error:
                _validate_order()

        exception = error.exception

        self.assertIsInstance(exception, ImproperlyConfigured)
        self.assertIs(order[0] in str(exception), True)
