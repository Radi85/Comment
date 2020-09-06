from django.dispatch import receiver
from django.db.models import signals

from comment.models import FlagInstance, ReactionInstance


@receiver(signals.post_delete, sender=FlagInstance)
def decrease_count(sender, instance, using, **kwargs):
    """Decrease flag count in the flag model before deleting an instance"""
    instance.flag.decrease_count()
    instance.flag.toggle_flagged_state()


@receiver(signals.post_delete, sender=ReactionInstance)
def delete_reaction_instance(sender, instance, using, **kwargs):
    instance.reaction.decrease_reaction_count(instance.reaction_type)
