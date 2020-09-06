from django.dispatch import receiver
from django.db.models import signals

from comment.models import Comment, Flag, FlagInstance, Reaction, ReactionInstance


@receiver(signals.post_save, sender=Comment)
def add_reaction(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        Reaction.objects.create(comment=instance)


@receiver(signals.post_save, sender=Comment)
def add_flag(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        Flag.objects.create(comment=instance)


@receiver(signals.post_save, sender=FlagInstance)
def increase_count(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        instance.flag.increase_count()
        instance.flag.toggle_flagged_state()


@receiver(signals.post_save, sender=ReactionInstance)
def add_count(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        instance.reaction.increase_reaction_count(instance.reaction_type)
