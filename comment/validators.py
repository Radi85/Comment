from abc import abstractmethod, ABCMeta

from django.contrib.contenttypes.models import ContentType
from django.core.validators import EmailValidator
from django.http import JsonResponse
from django.core.exceptions import ValidationError

from comment.exceptions import CommentBadRequest
from comment.messages import ContentTypeError, ExceptionError, EmailError
from comment.utils import get_request_data


class BaseValidatorMixin:
    __metaclass__ = ABCMeta
    api = False
    error = None

    def dispatch(self, request, *args, **kwargs):
        """
            let rest framework handle the exception to choose the right renderer
            validate method shall be called in the derived API class
        """
        if self.api:
            return super().dispatch(request, *args, **kwargs)
        try:
            self.validate(request)
        except CommentBadRequest as exc:
            return JsonResponse({'type': ExceptionError.ERROR_TYPE, 'detail': exc.detail}, status=400)
        return super().dispatch(request, *args, **kwargs)

    @abstractmethod
    def validate(self, request):
        pass


class ContentTypeValidator(BaseValidatorMixin):
    model_obj = None

    def validate_app_name(self, app_name):
        if not app_name:
            self.error = ContentTypeError.APP_NAME_MISSING
            raise CommentBadRequest(self.error)

        if not ContentType.objects.filter(app_label=app_name).exists():
            self.error = ContentTypeError.APP_NAME_INVALID.format(app_name=app_name)
            raise CommentBadRequest(self.error)
        return app_name

    def validate_model_name(self, model_name):
        if not model_name:
            self.error = ContentTypeError.MODEL_NAME_MISSING
            raise CommentBadRequest(self.error)
        return str(model_name).lower()

    def validate_content_type_object(self, app_name, model_name):
        try:
            ct_object = ContentType.objects.get(model=model_name, app_label=app_name)
        except ContentType.DoesNotExist:
            self.error = ContentTypeError.MODEL_NAME_INVALID.format(model_name=model_name)
            raise CommentBadRequest(self.error)
        return ct_object

    def validate_model_id(self, model_id):
        if not model_id:
            self.error = ContentTypeError.MODEL_ID_MISSING
            raise CommentBadRequest(self.error)
        try:
            model_id = int(model_id)
        except ValueError:
            self.error = ContentTypeError.ID_NOT_INTEGER.format(var_name='model', id=model_id)
            raise CommentBadRequest(self.error)
        return model_id

    def validate_model_object(self, app_name, model_name, model_id):
        ct_object = self.validate_content_type_object(app_name, model_name)
        model_class = ct_object.model_class()
        model_query = model_class.objects.filter(id=model_id)
        if not model_query.exists() and model_query.count() != 1:
            self.error = ContentTypeError.MODEL_ID_INVALID.format(model_id=model_id, model_name=model_name)
            raise CommentBadRequest(self.error)
        return model_query.first()

    def validate(self, request):
        super().validate(request)
        app_name = get_request_data(request, 'app_name', self.api)
        model_name = get_request_data(request, 'model_name', self.api)
        model_id = get_request_data(request, 'model_id', self.api)
        validated_app_name = self.validate_app_name(app_name)
        validated_model_name = self.validate_model_name(model_name)
        validated_model_id = self.validate_model_id(model_id)
        self.model_obj = self.validate_model_object(validated_app_name, validated_model_name, validated_model_id)


class ParentIdValidator(BaseValidatorMixin):
    parent_comment = None

    def validate_parent_id(self, parent_id):
        try:
            parent_id = int(parent_id)
        except ValueError:
            self.error = ContentTypeError.ID_NOT_INTEGER.format(var_name='parent', id=parent_id)
            raise CommentBadRequest(self.error)
        return parent_id

    def validate_comment_object(self, model_id, parent_id):
        from comment.models import Comment

        try:
            comment = Comment.objects.get(id=parent_id, object_id=model_id)
        except Comment.DoesNotExist:
            self.error = ContentTypeError.PARENT_ID_INVALID.format(parent_id=parent_id)
            raise CommentBadRequest(self.error)
        return comment

    def validate(self, request):
        super().validate(request)
        model_id = get_request_data(request, 'model_id', self.api)
        parent_id = get_request_data(request, 'parent_id', self.api)
        if not parent_id or parent_id == '0':
            return
        validated_parent_id = self.validate_parent_id(parent_id)
        self.parent_comment = self.validate_comment_object(model_id, validated_parent_id)


class ValidatorMixin(ContentTypeValidator, ParentIdValidator):
    pass


class DABEmailValidator(EmailValidator):
    def __init__(self, email):
        super().__init__(EmailError.EMAIL_INVALID)
        self.email = email

    def is_valid(self):
        try:
            self(self.email)
            return True
        except ValidationError:
            return False
