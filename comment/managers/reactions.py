from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models

from comment.messages import ReactionError


class ReactionManager(models.Manager):

    def get_reaction_object(self, comment):
        try:
            reaction = comment.reaction
        except ObjectDoesNotExist:
            reaction = self.create(comment=comment)
        return reaction


class ReactionInstanceManager(models.Manager):

    def clean_reaction_type(self, reaction_type):
        if isinstance(reaction_type, str):
            reaction = getattr(self.model().ReactionType, reaction_type.upper(), None)
            if reaction:
                return reaction.value

        raise ValidationError(ReactionError.TYPE_INVALID.format(reaction_type=reaction_type), code='invalid')

    def _delete_and_create_new_instance(self, instance, user, reaction_type):
        old_reaction_type = instance.reaction_type
        reaction_obj = instance.reaction
        instance.delete()
        if old_reaction_type != reaction_type:  # create the new instance
            reaction_obj.refresh_from_db()
            self.create(reaction=reaction_obj, user=user, reaction_type=reaction_type)

    def set_reaction(self, user, reaction, reaction_type):
        reaction_type = self.clean_reaction_type(reaction_type=reaction_type)
        created = False
        try:
            instance = self.get(reaction=reaction, user=user)
        except models.ObjectDoesNotExist:
            instance = self.create(reaction=reaction, user=user, reaction_type=reaction_type)
            created = True

        if not created:
            self._delete_and_create_new_instance(instance=instance, user=user, reaction_type=reaction_type)
