from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View

from comment.conf import settings
from comment.models import Comment, Flag, FlagInstance
from comment.utils import is_comment_admin, is_comment_moderator
from comment.mixins import CommentUpdateMixin, AJAXRequiredMixin


class FlagViewMixin(CommentUpdateMixin, AJAXRequiredMixin, View):
    comment = None

    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0):
            return HttpResponseForbidden(_('Flagging system must be enabled'))

        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)


class SetFlag(FlagViewMixin):

    def post(self, request, *args, **kwargs):
        response = {
            'status': 1
        }
        flag = Flag.objects.get_for_comment(self.comment)

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


class ChangeFlagState(FlagViewMixin):

    def dispatch(self, request, *args, **kwargs):
        self.comment = get_object_or_404(Comment, pk=self.kwargs.get('pk'))
        if not self.comment.is_flagged:
            raise PermissionDenied
        if not is_comment_admin(request.user) and not is_comment_moderator(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

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
