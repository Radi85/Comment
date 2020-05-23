from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from comment.managers import FlagManager, FlagInstanceManager
from comment.models import Comment


User = get_user_model()


class Flag(models.Model):

    comment = models.OneToOneField(Comment, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)
    moderator = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='flag_moderators')

    objects = FlagManager()
    state = models.SmallIntegerField(choices=objects.STATES, default=objects.states[0].value)

    def increase_count(self):
        """Increase flag count and save the model """
        self.refresh_from_db()
        self.count = models.F('count') + 1
        self.save()

    def decrease_count(self):
        """Decrease flag count and save the model """
        self.refresh_from_db()
        if self.count > 0:
            self.count = models.F('count') - 1
            self.save()

    @property
    def comment_author(self):
        return self.comment.user


class FlagInstance(models.Model):

    flag = models.ForeignKey(Flag, on_delete=models.CASCADE, related_name='flags')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flags')
    info = models.TextField(null=True, blank=False)
    date_flagged = models.DateTimeField(auto_now=timezone.now())

    objects = FlagInstanceManager()
    reason = models.SmallIntegerField(choices=objects.REASONS, default=objects.reason_values[0])

    class Meta:
        unique_together = ('flag', 'user')
        ordering = ('date_flagged',)

    def save(self, *args, **kwargs):
        """Increase reaction count in the reaction model after saving an instance"""
        super().save(*args, **kwargs)
        self.flag.increase_count()


@receiver(post_delete, sender=FlagInstance)
def delete_flag_instance(sender, instance, using, **kwargs):
    """Decrease flag count in the flag model before deleting an instance"""
    instance.flag.decrease_count()


@receiver(post_save, sender=Comment)
def add_reaction(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        Flag.objects.create(comment=instance)
