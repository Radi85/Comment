from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View

from comment.models import Comment, Flag, FlagInstance
from comment.mixins import CanSetFlagMixin, CanEditFlagStateMixin


class SetFlag(CanSetFlagMixin, View):
    comment = None

    def get_object(self):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        return self.comment

    def post(self, request, *args, **kwargs):
        data = {
            'status': 1
        }
        flag = Flag.objects.get_for_comment(self.comment)

        try:
            if FlagInstance.objects.set_flag(request.user, flag, **request.POST.dict()):
                data['msg'] = _('Comment flagged')
                data['flag'] = 1
            else:
                data['msg'] = _('Comment flag removed')

            data.update({
                'status': 0
            })
        except ValidationError as e:
            data.update({
                'msg': e.messages
            })

        return JsonResponse(data)


class ChangeFlagState(CanEditFlagStateMixin, View):
    comment = None

    def get_object(self):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        return self.comment

    def post(self, request, *args, **kwargs):
        state = request.POST.get('state')
        try:
            self.comment.flag.toggle_state(state, request.user)
        except ValidationError:
            return JsonResponse({'state': 0})
        response = {
            'state': self.comment.flag.state
        }
        return JsonResponse(response)
