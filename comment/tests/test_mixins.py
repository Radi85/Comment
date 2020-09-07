from rest_framework import status

from comment.mixins import AJAXRequiredMixin, ContentTypeMixin, ParentIdMixin
from comment.tests.base import BaseCommentMixinTest


class AJAXMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.mixin = AJAXRequiredMixin()

    def test_non_ajax_request(self):
        request = self.factory.get('/')
        response = self.mixin.dispatch(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content.decode('utf-8'), 'Only AJAX request are allowed')


class ContentTypeMixinTest(BaseCommentMixinTest):
    def setUp(self):
        super().setUp()
        self.mixin = ContentTypeMixin()
        self.mixin.api = True
        self.base_url = '/api/comments/'

    def test_missing_app_name(self):
        url_data = self.url_data.copy()
        url_data.pop('app_name')
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, 'app name must be provided')

    def test_missing_model_type(self):
        url_data = self.url_data.copy()
        url_data.pop('model_name')
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, 'model name must be provided')

    def test_missing_model_id(self):
        url_data = self.url_data.copy()
        url_data.pop('model_id')
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, 'model id must be provided')

    def test_invalid_model_name(self):
        url_data = self.url_data.copy()
        model_name = 'not exists'
        url_data['model_name'] = model_name
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, f'{model_name} is NOT a valid model name')

    def test_invalid_app_name(self):
        url_data = self.url_data.copy()
        app_name = 'not exists'
        url_data['app_name'] = app_name
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, f'{app_name} is NOT a valid app name')

    def test_model_id_does_not_exist(self):
        url_data = self.url_data.copy()
        model_id = 100
        url_data['model_id'] = model_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, f'{model_id} is NOT a valid model id for the model {url_data["model_name"]}')

    def test_model_id_non_integral(self):
        url_data = self.url_data.copy()
        model_id = 'not integral'
        url_data['model_id'] = model_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, f'model id must be an integer, {model_id} is NOT')


class TestParentIdMixin(BaseCommentMixinTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_comment(cls.content_object_1)
        cls.create_comment(cls.content_object_2)
        cls.mixin = ParentIdMixin()
        cls.mixin.api = True
        cls.base_url = '/api/comments/create/'

    def test_parent_id_not_int(self):
        # parent id not int
        parent_id = 'c'
        url_data = self.url_data.copy()
        url_data['parent_id'] = parent_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.mixin.error, f'the parent id must be an integer, {parent_id} is NOT')

    def test_parent_id_does_not_exist(self):
        parent_id = 100
        url_data = self.url_data.copy()
        url_data['parent_id'] = parent_id
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.mixin.error,
            (
                f'{parent_id} is NOT a valid id for a parent comment or '
                'the parent comment does NOT belong to this model object'
            )
        )

    def test_parent_id_does_not_belong_to_provided_model_type(self):
        # parent id doesn't belong to the provided model type
        parent_id = 100
        url_data = self.url_data.copy()
        url_data.update({'model_id': 2, 'parent_id': parent_id})
        request = self.factory.get(self.get_url(**url_data))
        response = self.mixin.dispatch(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.mixin.error,
            (
                f'{parent_id} is NOT a valid id for a parent comment or '
                'the parent comment does NOT belong to this model object'
            )
        )
