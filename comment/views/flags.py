from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.views import View

from comment.models import Comment, Flag, FlagInstance
from comment.mixins import CanSetFlagMixin, CanUpdateFlagStateMixin, BaseCommentMixin
from comment.responses import UTF8JsonResponse, DABResponseData
from comment.messages import FlagInfo, FlagError


class SetFlag(CanSetFlagMixin, BaseCommentMixin, View, DABResponseData):
    comment = None

    def get_object(self):
        self.comment = get_object_or_404(
            Comment.objects.select_related('user', 'reaction', 'flag'),
            pk=self.kwargs.get('pk')
        )
        return self.comment

    def post(self, request, *args, **kwargs):
        self.data = {
            'status': 1
        }
        flag = Flag.objects.get_for_comment(self.comment)

        try:
            if FlagInstance.objects.set_flag(request.user, flag, **request.POST.dict()):
                self.msg = FlagInfo.FLAGGED_SUCCESS
                self.data['flag'] = 1
            else:
                self.msg = FlagInfo.UNFLAGGED_SUCCESS

            self.data.update({'status': 0})
            self.status = 200
        except ValidationError as e:
            self.error = e.message
            self.status = 400

        return UTF8JsonResponse(self.json(), status=self.status)


class ChangeFlagState(CanUpdateFlagStateMixin, View, DABResponseData):
    comment = None

    def get_object(self):
        self.comment = get_object_or_404(
            Comment.objects.select_related('user', 'reaction', 'flag'),
            pk=self.kwargs.get('pk')
        )
        return self.comment

    def post(self, request, *args, **kwargs):
        state = request.POST.get('state')
        try:
            self.comment.flag.toggle_state(state, request.user)
            self.status = 200
        except ValidationError:
            self.error = FlagError.STATE_CHANGE_ERROR
            self.status = 400

        self.data = {
            'state': self.comment.flag.state
        }
        return UTF8JsonResponse(self.json(), status=self.status)
