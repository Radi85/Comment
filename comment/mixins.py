from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _


# This willl be expanded to provide checks for validating the form fields
class BaseCommentMixin(LoginRequiredMixin):
    pass


class AJAXRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest(_('Only AJAX request are allowed'))
        return super().dispatch(request, *args, **kwargs)
