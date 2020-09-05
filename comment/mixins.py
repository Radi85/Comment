from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from comment.models import Comment
from comment.utils import get_data_for_request, get_response_for_bad_request


class CommentUpdateMixin(LoginRequiredMixin):
    pass


class AJAXRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.META.get('HTTP_X_REQUESTED_WITH', None) == 'XMLHttpRequest':
            return get_response_for_bad_request(why='Only AJAX request are allowed')
        return super().dispatch(request, *args, **kwargs)


class ContentTypeMixin:
    """
    When using this with DRF intialize `api=True` in the class.
    Used for provinding validation of query parameters in request to match
    a valid ContentType. Upon successful validation, `model_name`, `model_id`, `app_name`
    can be accessed directly as class attributes.
    """
    api = False
    error = ''

    def _set_model_name_or_error(self, val):
        if not val:
            self.error = "model name must be provided"
            return
        self.model_name = val

    def _set_model_id_or_error(self, val):
        if not val:
            self.error = "model id must be provided"
            return
        self.model_id = val

    def _set_app_name_or_error(self, val):
        if not val:
            self.error = 'app name must be provided'
            return

        if not ContentType.objects.filter(app_label=val).exists():
            self.error = f'{val} is NOT a valid app name'
            return
        self.app_name = val

    def _set_error(self):
        try:
            model_name = self.model_name.lower()
            ct = ContentType.objects.get(model=model_name).model_class()
            model_class = ct.objects.filter(id=self.model_id)
            if not model_class.exists() and model_class.count() != 1:
                self.error = f"{self.model_id} is NOT a valid model id for the model {self.model_name}"
        except ContentType.DoesNotExist:
            self.error = f"{self.model_name} is NOT a valid model name"
        except ValueError:
            self.error = f"model id must be an integer, {self.model_id} is NOT"

    def dispatch(self, request, *args, **kwargs):
        data = get_data_for_request(request, self.api)
        self._set_app_name_or_error(data.get('app_name'))
        self._set_model_name_or_error(data.get('model_name'))
        self._set_model_id_or_error(data.get('model_id'))
        if not self.error:
            self._set_error()
        if self.error:
            return get_response_for_bad_request(why=self.error, api=self.api)
        return super().dispatch(request, *args, **kwargs)


class ParentIdMixin:
    """
    When using this with DRF intialize `api=True` in the class.
    Use this mixin only after ContentTypeMixin otherwise `model_id` might not be defined.
    Used for provinding validation of query parameter `parent_id` in request to match
    a valid parent comment. Upon successful validation, `parent_id` can be accessed
    directly as a class attribute.
    """
    api = False
    error = ''

    def _clean_parent_id(self, val):
        if not val or val == '0':
            val = None
        return val

    def _set_parent_id_or_error(self, val):
        if val:
            model_id = self.data.get('model_id')
            try:
                if not Comment.objects.filter(id=val, object_id=model_id).exists():
                    self.error = _(
                        f'{val} is NOT a valid id for a parent comment or '
                        'the parent comment does NOT belong to this model object'
                        )
                    return
            except ValueError:
                self.error = f"the parent id must be an integer, {val} is NOT"
                return
        self.parent_id = val

    def dispatch(self, request, *args, **kwargs):
        self.data = get_data_for_request(request, self.api)
        parent_id = self._clean_parent_id(self.data.get('parent_id'))
        self._set_parent_id_or_error(parent_id)
        if self.error:
            return get_response_for_bad_request(why=self.error, api=self.api)
        return super().dispatch(request, *args, **kwargs)
