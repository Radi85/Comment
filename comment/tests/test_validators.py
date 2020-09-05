from django.http import JsonResponse
from django.test import TestCase
from django.views import View
from rest_framework import status
from rest_framework.generics import ListAPIView

from comment.tests.base import BaseCommentMixinTest
from comment.validators import CommentBadRequest, ValidatorMixin


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
        self.assertEqual(validator.detail, "Bad Request")

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
        self.assertEqual(self.view.error, 'app name must be provided')

    def test_missing_model_type(self):
        url_data = self.data.copy()
        url_data.pop('model_name')
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, 'model name must be provided')

    def test_missing_model_id(self):
        url_data = self.data.copy()
        url_data.pop('model_id')
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, 'model id must be provided')

    def test_invalid_model_name(self):
        url_data = self.data.copy()
        model_name = 'not exists'
        url_data['model_name'] = model_name
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, f'{model_name} is NOT a valid model name')

    def test_invalid_app_name(self):
        url_data = self.data.copy()
        app_name = 'not exists'
        url_data['app_name'] = app_name
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, f'{app_name} is NOT a valid app name')

    def test_model_id_does_not_exist(self):
        url_data = self.data.copy()
        model_id = 100
        url_data['model_id'] = model_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, f'{model_id} is NOT a valid model id for the model {url_data["model_name"]}')

    def test_model_id_non_integral(self):
        url_data = self.data.copy()
        model_id = 'not integral'
        url_data['model_id'] = model_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, f'model id must be an integer, {model_id} is NOT')

    def test_not_valid_parent_id(self):
        url_data = self.data.copy()
        parent_id = 1000
        url_data['parent_id'] = parent_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.view.error,
            (f'{parent_id} is NOT a valid id for a parent comment or '
             'the parent comment does NOT belong to the provided model object')
        )

    def test_parent_id_no_int(self):
        url_data = self.data.copy()
        parent_id = 'string'
        url_data['parent_id'] = parent_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.view.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.view.error, f'the parent id must be an integer, {parent_id} is NOT')

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
