from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from comment.models import Comment, Flag, FlagInstance
from comment.mixins import CanSetFlagMixin, CanEditFlagStateMixin
from comment.messages import FlagInfo


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
                data['msg'] = FlagInfo.FLAGGED_SUCCESS
                data['flag'] = 1
            else:
                data['msg'] = FlagInfo.UNFLAGGED_SUCCESS

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
