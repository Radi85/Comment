from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_POST

from comment.models import Comment, Flag, FlagInstance


@method_decorator(require_POST, name='dispatch')
class SetFlag(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if not getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0):
            return HttpResponseForbidden(_('Flagging system must be enabled'))

        if not request.is_ajax():
            return HttpResponseBadRequest(_('Only AJAX request are allowed'))

        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        response = {
            'status': 1
        }
        flag = Flag.objects.get_flag_object(comment)

        try:
            if FlagInstance.objects.set_flag(request.user, flag, **request.POST.dict()):
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
