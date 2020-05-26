from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_POST

from comment.models import Comment, FlagInstance


@method_decorator(require_POST, name='dispatch')
class SetFlag(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest(_('Only AJAX request are allowed'))
        
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        reason = request.POST.get('reason', None)
        info = request.POST.get('info', None)
        response = {
            'status': 1
        }
        try:
            if FlagInstance.objects.set_flag(request.user, comment.flag, reason, info):
                response['msg'] = _('Comment flagged')
            else:
                response.update['msg'] = _('Comment flag removed')
            
            response.update({
                'status': 0
            })
        except ValidationError as e:
            response.update({
                'msg': e.message
            })

        return JsonResponse(response)
