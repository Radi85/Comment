from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from comment.models import Comment, Reaction, ReactionInstance
from comment.mixins import BaseCommentMixin
from comment.messages import ReactionInfo


@method_decorator(require_POST, name='dispatch')
class SetReaction(BaseCommentMixin, View):

    @staticmethod
    def post(request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        reaction_type = kwargs.get('reaction', None)
        reaction_obj = Reaction.objects.get_reaction_object(comment)
        try:
            ReactionInstance.objects.set_reaction(user=request.user, reaction=reaction_obj, reaction_type=reaction_type)
        except ValidationError as e:
            return HttpResponseBadRequest(e.messages)

        comment.reaction.refresh_from_db()
        response = {
            'status': 0,
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'msg': ReactionInfo.UPDATED_SUCCESS
        }
        return JsonResponse(response)
