from collections import namedtuple
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from comment.manager.reactions import ReactionManager
from comment.models.comments import Comment

REACTION_CHOICES = [
    (1, _('like')),
    (2, _('dislike'))
]

# construct a named tuple
choices = namedtuple('reaction_choices', ['value', 'reaction'])

# construct the list of named tuple
reaction_choices = [choices(*reaction) for reaction in REACTION_CHOICES]


class Reaction(models.Model):
    reactions = models.SmallIntegerField(choices=REACTION_CHOICES, default=reaction_choices[0].value)
    comment = models.ForeignKey(Comment, related_name='comment_reaction', on_delete=models.CASCADE)
    
    objects = models.Manager()
    comment_objects = ReactionManager()

    def _get_reaction_count(self, value:int)->int:
        """
        Returns total count of a reaction

        Args:
            value (int): integeral value mapped to the reaction in database
        """
        return Reaction.objects.filter(comment=self.comment,reactions=value).count()
    
    def _get_reaction_users(self, value:int)->List[get_user_model()]:
        """
        Return list of users that have had a particular reaction
        
        Args:
            value (int): integeral value mapped to the reaction in database    
        """
        return Reaction.comment_objects.filter(reaction=value).values_list('comment__user')


    @property
    def likes(self)-> int:
        """
        Returns total number of likes for a comment
        """
        return self._get_reaction_count(value=reaction_choices[0].value)

    @property
    def dislikes(self)-> int:
        """
        Returns total number of dislikes for a comment
        """
        return self._get_reaction_count(value=reaction_choices[1].value)

    @property
    def liked_users(self)->List[get_user_model()]:
        """Returns list of all users that have liked this comment"""
        return self._get_reaction_users(value=reaction_choices[0].value)

    @property
    def disliked_users(self)->List[get_user_model()]:
        """Returns list of all users that have disliked this comment"""
        return self._get_reaction_users(value=reaction_choices[1].value)


class ReactionInstance(models.Model):
    reaction = models.ForeignKey(Reaction, related_name='reaction', on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name='user', on_delete=models.CASCADE)
    date_reacted = models.DateTimeField(auto_now=timezone.now())

    class Meta:
        unique_together = ['user', 'reaction']

#  def create_reaction(self, user:get_user_model(), reaction:Reaction):
#     """[summary]
    
#     Args:
#         reaction ([type]): [description]
#     """
#         if ReactionInstance.objects.filter(user=user, )