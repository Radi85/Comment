from enum import IntEnum, unique

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from comment.manager.reactions import ReactionManager
from comment.models import Comment


class Reaction(models.Model):
    comment = models.ForeignKey(Comment, related_name='reactions', on_delete=models.CASCADE)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    
    objects = models.Manager()
    comment_objects = ReactionManager()
    
    def _increase_likes(self):
        """Increase likes and save the model"""
        self.likes = models.F('likes') + 1
        self.save()

    def _increase_dislikes(self):
        """Increase dislikes and save the model"""
        self.dislikes = models.F('dislikes') + 1
        self.save()
    
    def _decrease_likes(self):
        """Decrease likes and save the model"""
        if self.likes > 0:
            self.likes = models.F('likes') - 1
            self.save()

    def _decrease_dislikes(self):
        """Decrease dislikes and save the model"""
        if self.dislikes > 0:
            self.dislikes = models.F('dislikes') - 1
            self.save()

    def _increase_reaction_count(self, reaction):
        """
        Increase reaction count(likes/dislikes)

        Args:
            reaction (int): The integral value that matches to the reaction value in
                the database
            
        Returns:
            None
        """
        if reaction == ReactionInstance.ReactionType.LIKE.value:
            self._increase_likes()
        else:
            self._increase_dislikes()

    def _decrease_reaction_count(self, reaction):
        """
        Decrease reaction count(likes/dislikes)

        Args:
            reaction (int): The integral value that matches to the reaction value in
                the database

        Returns:
            None
        """
        if reaction == ReactionInstance.ReactionType.LIKE.value:
            self._decrease_likes()
        else:
            self._decrease_dislikes()


class ReactionInstance(models.Model):

    @unique
    class ReactionType(IntEnum):
        LIKE = 1
        DISLIKE = 2

    reaction_choices = [(r.value, r.name) for r in ReactionType]

    reaction = models.ForeignKey(Reaction, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name='reactions', on_delete=models.CASCADE)
    reaction_type = models.SmallIntegerField(choices=reaction_choices)
    date_reacted = models.DateTimeField(auto_now=timezone.now())

    class Meta:
        unique_together = ['user', 'reaction']

    @classmethod
    def clean_reaction_type(cls, reaction_type):
        """
        Check if the reaction is a valid one or not

        Args:
            reaction_type (str): The reaction to be saved

        Returns:
            int: The integral value that matches to the reaction value in
                the database
        """
        reaction = getattr(cls.ReactionType, reaction_type.upper(), None)
        if not reaction:
            return ValidationError(
                _('%(reaction)s is an invalid reaction'), 
                code='invalid',
                params={'reaction':reaction}
                )
        return reaction.value

    def save(self, *args, **kwargs):
        """
        Increase reaction count in the reaction model after saving an instance

        Args:
            reaction_type (int): The integral value that matches to the reaction value in
                the database
        """
        super().save(*args, **kwargs)
        reaction = self.reaction
        reaction_type = self.reaction_type
        reaction._increase_reaction_count(reaction_type)

    @classmethod
    def _delete_and_create_new_instance(cls, instance, user, reaction_type):
        """
        Delete the previous instance and create a new instance

        Args:
            instance (ReactionInstance): the instance to be deleted
            user (`get_user_model`): the user to be associated to the reaction
            reaction_type (int): The integral value that matches to the reaction value in
                the database
        
        Returns:
            None
        """
        old_reaction_type = instance.reaction_type
        reaction_obj = instance.reaction
        instance.delete()
        if old_reaction_type != reaction_type:  # create the new instance
            reaction_obj.refresh_from_db()
            ReactionInstance.objects.create(
                reaction=reaction_obj,
                user=user,
                reaction_type=reaction_type
                )

    @classmethod
    def set_reaction(cls, user, comment, reaction_type):
        """
        Set a reaction and update its count

        Args:
            user (`get_user_model()`): user.
            comment (`Comment`): the comment that needs to record the reaction.
            reaction (str): the reaction that needs to be added.

        Returns:
            bool: Returns True if a reaction is updated successfully
        """
        reaction_type = cls.clean_reaction_type(reaction_type=reaction_type)
        reaction_obj = Reaction.objects.get(comment=comment)
        try:
            created = False
            instance = ReactionInstance.objects.get(
                reaction=reaction_obj,
                user=user
                )
        except models.ObjectDoesNotExist:
            instance = ReactionInstance.objects.create(
                reaction=reaction_obj,
                user=user,
                reaction_type=reaction_type
            )
            created = True

        if not created:
            cls._delete_and_create_new_instance(
                instance=instance,
                user=user,
                reaction_type=reaction_type
                )

        return True

@receiver(post_delete, sender=ReactionInstance)
def delete_reaction_instance(sender, instance, using, **kwargs):
    """Decrease reaction count in the reaction model before deleting an instance"""
    old_reaction_type = instance.reaction_type
    reaction = instance.reaction
    reaction._decrease_reaction_count(old_reaction_type)