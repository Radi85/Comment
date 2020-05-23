from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_POST

from comment.models import Comment, ReactionInstance


@method_decorator(require_POST, name='dispatch')
class SetReaction(LoginRequiredMixin, View):

    @staticmethod
    def _clean_reaction(reaction):
        if (not isinstance(reaction, str)) or (not getattr(ReactionInstance.ReactionType, reaction.upper(), None)):
            return None
        return reaction.lower()

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        if not request.is_ajax():
            return HttpResponseBadRequest('Only AJAX request are allowed')

        reaction = kwargs.get('reaction', None)
        reaction_type = self._clean_reaction(reaction)
        if not reaction_type:
            return HttpResponseBadRequest(_('This is not a valid reaction'))
        ReactionInstance.objects.set_reaction(user=request.user, reaction=comment.reaction, reaction_type=reaction_type)
        comment.reaction.refresh_from_db()
        response = {
            'status': 0,
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'msg': _('Your reaction has been updated successfully')
        }
        return JsonResponse(response)
