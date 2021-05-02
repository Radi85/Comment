from django.views import View

from comment.models import BlockedUser, BlockedUserHistory, Comment
from comment.mixins import CanBlockUsersMixin
from comment.responses import UTF8JsonResponse, DABResponseData
from comment.messages import BlockUserError


class BaseToggleBlockingView(DABResponseData):
    response_class = None

    def get_response_class(self):
        assert self.response_class is not None, (
                "'%s' should either include a `response_class` attribute, "
                "or override the `get_response_class()` method."
                % self.__class__.__name__
        )
        return self.response_class

    def post(self, request, *args, **kwargs):
        response_class = self.get_response_class()
        request_data = request.POST or getattr(request, 'data', {})
        comment_id = request_data.get('comment_id', None)
        try:
            comment = Comment.objects.get(id=int(comment_id))
        except (Comment.DoesNotExist, ValueError, TypeError):
            self.error = {
                'detail': BlockUserError.INVALID
            }
            self.status = 400
            return response_class(self.json(), status=self.status)

        blocked_user, created = BlockedUser.objects.get_or_create_blocked_user_for_comment(comment)

        if not created:
            blocked_user.blocked = not blocked_user.blocked
        blocked_user.save()

        reason = request_data.get('reason', None)
        if blocked_user.blocked and not reason:
            reason = comment.content

        BlockedUserHistory.objects.create_history(
            blocked_user=blocked_user,
            blocker=request.user,
            reason=reason
        )
        self.data = {
            'blocked_user': comment.get_username(),
            'blocked': blocked_user.blocked,
            'urlhash': comment.urlhash
        }
        return response_class(self.json())


class ToggleBlockingView(CanBlockUsersMixin, BaseToggleBlockingView, View):
    response_class = UTF8JsonResponse
