from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from comment.manager.reactions import ReactionManager
from comment.models import Comment


class Reaction(models.Model):

    comment = models.ForeignKey(Comment, related_name='comment_reaction', on_delete=models.CASCADE)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    
    objects = models.Manager()
    comment_objects = ReactionManager()
    
    def increase_likes(self):
        """Increase likes and save the model"""
        self.likes = models.F('likes') + 1
        self.save()

    def increase_dislikes(self):
        """Increase dislikes and save the model"""
        self.dislikes = models.F('dislikes') + 1
        self.save()
    
    def decrease_likes(self):
        """Decrease likes and save the model"""
        if self.likes > 0:
            self.likes = models.F('likes') - 1
            self.save()

    def decrease_dislikes(self):
        """Decrease dislikes and save the model"""
        if self.dislikes > 0:
            self.dislikes = models.F('dislikes') - 1
            self.save()

    def _increase_reaction_count(self, reaction):
        """
        Increase reaction count(likes/dislikes)

        Args:
            reaction ([int]): The integral value that matches to the reaction value in
                the database
            
        Returns:
            None
        """
        if reaction == ReactionInstance.ReactionType['LIKE']:
            self.increase_likes()
        else:
            self.increase_dislikes()

    def _decrease_reaction_count(self, reaction):
        """
        Decrease reaction count(likes/dislikes)

        Args:
            reaction ([int]): The integral value that matches to the reaction value in
                the database

        Returns:
            None
        """
        if reaction == ReactionInstance.ReactionType['LIKE']:
            self.decrease_likes()
        else:
            self.decrease_dislikes()

    def update_reaction(self, user, comment, reaction):
        """
        Update a Reaction

        Args:
            user (`get_user_model()`): user.
            comment (`Comment`): the comment that needs to record the reaction.
            reaction (str): the reaction that needs to be added.

        Returns:
            bool: Returns True if a reaction is updated successfully
        """
        # Check if the reaction is a valid one or not
        try:
            reaction_type = ReactionInstance.ReactionType[reaction.upper()]
        except KeyError:
            return ValidationError(_('%(reaction_type)s is an invalid reaction'), code='invalid', params={'reaction':reaction})
        
        # Currently, all reaction fields are mutually exclusive
        old_reaction, created = ReactionInstance.objects.get_or_create(reaction=self, user=user)

        if created:
            self._increase_reaction_count(reaction_type)

        else:
            old_reaction_type = old_reaction.reaction_type
            old_reaction.delete()
            if old_reaction_type == reaction_type:  # decrease count
                self._decrease_reaction_count(reaction_type)
            else:   # decrease count for the old reaction, create and increment for the new one
                self._decrease_reaction_count(old_reaction_type)
                self.refresh_from_db()
                ReactionInstance.objects.create(reaction=self, user=user, reaction_type=reaction_type)
                self._increase_reaction_count(reaction_type)
            
        return True


class ReactionInstance(models.Model):
    
    class ReactionType(models.IntegerChoices):
        LIKE = 1, _('Like')
        DISLIKE = 2, _('Dislike')
    
    reaction = models.ForeignKey(Reaction, related_name='reaction', on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name='user', on_delete=models.CASCADE)
    reaction_type = models.SmallIntegerField(choices=ReactionType.choices, default=ReactionType.LIKE)
    date_reacted = models.DateTimeField(auto_now=timezone.now())

    class Meta:
        unique_together = ['user', 'reaction']
