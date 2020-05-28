from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_POST

from comment.models import Comment, Flag, FlagInstance


@method_decorator(require_POST, name='dispatch')
class SetFlag(LoginRequiredMixin, View):
    def _get_flag_object(self, comment):
        try:
            flag = comment.flag
        except ObjectDoesNotExist:
            flag = Flag.objects.create(comment=comment)
        return flag

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest(_('Only AJAX request are allowed'))

        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        response = {
            'status': 1
        }
        flag = self._get_flag_object(comment)

        try:
            if FlagInstance.objects.set_flag(request.user, flag, data=request.POST):
                response['msg'] = _('Comment flagged')
                response['flag'] = 1
            else:
                response['msg'] = _('Comment flag removed')

            response.update({
                'status': 0
            })
        except ValidationError as e:
            response.update({
                'msg': e.messages
            })

        return JsonResponse(response)
