from abc import abstractmethod, ABCMeta

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse

from comment.models import Comment
from comment.exceptions import CommentBadRequest
from comment.messages import ContentTypeError, ExceptionError


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
    app_name = None
    model_name = None
    model_id = None

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
        app_name = request.GET.get("app_name") or request.POST.get("app_name")
        model_name = request.GET.get("model_name") or request.POST.get("model_name")
        model_id = request.GET.get("model_id") or request.POST.get("model_id")
        self.app_name = self.validate_app_name(app_name)
        self.model_name = self.validate_model_name(model_name)
        self.model_id = self.validate_model_id(model_id)
        self.validate_model_object(self.app_name, self.model_name, self.model_id)


class ParentIdValidator(BaseValidatorMixin):
    parent_id = None

    def validate_parent_id(self, parent_id):
        try:
            parent_id = int(parent_id)
        except ValueError:
            self.error = ContentTypeError.ID_NOT_INTEGER.format(var_name='parent', id=parent_id)
            raise CommentBadRequest(self.error)
        return parent_id

    def validate_comment_object(self, model_id, parent_id):
        try:
            comment = Comment.objects.get(id=parent_id, object_id=model_id)
        except Comment.DoesNotExist:
            self.error = ContentTypeError.PARENT_ID_INVALID.format(parent_id=parent_id)
            raise CommentBadRequest(self.error)
        return comment

    def validate(self, request):
        super().validate(request)
        model_id = request.GET.get("model_id") or request.POST.get("model_id")
        parent_id = request.GET.get("parent_id") or request.POST.get("parent_id")
        if not parent_id or parent_id == '0':
            return
        self.parent_id = self.validate_parent_id(parent_id)
        self.validate_comment_object(model_id, self.parent_id)


class ValidatorMixin(ContentTypeValidator, ParentIdValidator):
    pass
