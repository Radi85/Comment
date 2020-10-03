from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.http import JsonResponse

from django.views.generic.base import View

from comment.models import Follower
from comment.mixins import CanSubscribeMixin
from comment.validators import ContentTypeValidator
from comment.messages import FollowError


class BaseToggleFollowView(ContentTypeValidator):
    response_class = None

    def get_response_class(self):
        assert self.response_class is not None, (
                "'%s' should either include a `response_class` attribute, "
                "or override the `get_response_class()` method."
                % self.__class__.__name__
        )
        return self.response_class

    def post(self, request, *args, **kwargs):
        """ Allow authenticated users only, anonymous may be added in the future """
        email = request.POST.get('email', None)
        response_class = self.get_response_class()
        if email:
            email_validator = EmailValidator(FollowError.EMAIL_INVALID)
            try:
                email_validator(email)
            except ValidationError as error:
                return response_class({'invalid_email': error.messages}, status=400)

        user = request.user
        if user.email:
            email = user.email

        if not email:
            return response_class({
                'email_required': True,
                'message': FollowError.EMAIL_REQUIRED.format(model_object=str(self.model_obj))
            }, status=400)

        if not user.email:
            user.email = email
            user.save()

        username = user.username or email.aplit('@')[0]
        following = Follower.objects.toggle_follow(email=email, model_object=self.model_obj, username=username)
        return response_class({
            'following': following,
            'app_name': self.model_obj._meta.app_label,
            'model_name': self.model_obj.__class__.__name__,
            'model_id': self.model_obj.id,
            'model_object': str(self.model_obj)
        }, status=200)


class ToggleFollowView(BaseToggleFollowView, CanSubscribeMixin, View):
    response_class = JsonResponse
