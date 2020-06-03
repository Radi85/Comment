from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.http import require_POST

from comment.models import Comment, Reaction, ReactionInstance


@method_decorator(require_POST, name='dispatch')
class SetReaction(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, id=kwargs.get('pk'))
        if not request.is_ajax():
            return HttpResponseBadRequest(_('Only AJAX request are allowed'))

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
            'msg': _('Your reaction has been updated successfully')
        }
        return JsonResponse(response)
