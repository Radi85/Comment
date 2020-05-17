from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic.detail import SingleObjectMixin

from comment.models import Comment, ReactionInstance


@method_decorator(require_POST, name='dispatch')
class SetReaction(LoginRequiredMixin, SingleObjectMixin, View):
    model = Comment

    def _clean_reaction(self, reaction):
        """
        Clean reaction coming in the URL

        Args:
            reaction (str): the reaction passed to the URL

        Returns:
            False: when reaction is not an acceptable string.
            str: when acceptable, the reaction in lower case form.
        """
        if not getattr(ReactionInstance.ReactionType, reaction.upper(), None):
            return False
        return reaction.lower()

    def post(self, request, *args, **kwargs):
        """Record reaction and return an appropriate response"""
        if not request.is_ajax():
            return HttpResponseBadRequest('Only AJAX request are allowed')

        reaction = kwargs.get('reaction', None)
        reaction_type = self._clean_reaction(reaction)

        if not reaction_type:
            return HttpResponseBadRequest(_('This is not a valid reaction'))

        comment = self.get_object()
        ReactionInstance.set_reaction(user=request.user, comment=comment, reaction_type=reaction_type)
        response = {
            'status': 0,
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'msg': _('Your reaction has been updated successfully')
        }
        return JsonResponse(response)
