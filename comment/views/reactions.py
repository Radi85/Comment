from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from comment.models import Comment, ReactionInstance


@require_POST
@login_required
def react(request, comment_id, reaction):
    """
    Record reaction and return an appropriate response

    Args:
        request (WSGI object): [description]
        comment_id (int): primary key of the comment that needs to record comment.
        reaction (str): the reaction to be recorded
    """
    if not request.is_ajax():
        return HttpResponseBadRequest('Only AJAX request are allowed')

    comment = get_object_or_404(Comment, id=comment_id)
    response = {
        'status': 1,
        'msg': _('Sorry we could not update this reaction. Please try again.')
    }
    if ReactionInstance.set_reaction(user=request.user, comment=comment, reaction_type=reaction):
        response.update({
            'status': 0,
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'msg': _('Your action has been updated successfully')
        })
    return JsonResponse(response)
