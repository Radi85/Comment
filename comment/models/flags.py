from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from comment.managers import FlagManager, FlagInstanceManager
from comment.models import Comment


User = get_user_model()


class Flag(models.Model):
    UNFLAGGED = 1
    FLAGGED = 2
    REJECTED = 3
    RESOLVED = 4
    STATES_CHOICES = [
        (UNFLAGGED, 'Unflagged'),
        (FLAGGED, 'Flagged'),
        (REJECTED, 'Flag rejected by the moderator'),
        (RESOLVED, 'Comment modified by the author'),
    ]

    comment = models.OneToOneField(Comment, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)
    state = models.SmallIntegerField(choices=STATES_CHOICES, default=UNFLAGGED)
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    objects = FlagManager()

    def increase_count(self):
        """Increase flag count and save the model """
        self.refresh_from_db()
        field = 'count'
        self.count = models.F(field) + 1
        self.save(update_fields=[field])

    def decrease_count(self):
        """Decrease flag count and save the model """
        self.refresh_from_db()
        field = 'count'
        self.count = models.F(field) - 1
        self.save(update_fields=[field])

    @property
    def comment_author(self):
        return self.comment.user

    def get_verbose_state(self, state):
        state = self.get_clean_state(state)
        for item in self.STATES_CHOICES:
            if item[0] == state:
                return item[1]
        return None

    @property
    def is_flag_enabled(self):
        return bool(getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0))

    def get_clean_state(self, state):
        err = ValidationError(_('%(state)s is an invalid state'), code='invalid', params={'state': state})
        try:
            state = int(state)
            if state not in [st[0] for st in self.STATES_CHOICES]:
                raise err
        except (ValueError, TypeError):
            raise err
        return state

    def toggle_state(self, state, moderator):
        state = self.get_clean_state(state)
        # toggle states occurs between rejected and resolved states only
        if state != self.REJECTED and state != self.RESOLVED:
            raise ValidationError(_('%(state)s is an invalid state'), code='invalid', params={'state': state})
        if self.state == state:
            self.state = self.FLAGGED
        else:
            self.state = state
        self.moderator = moderator
        self.save()

    def toggle_flagged_state(self):
        allowed_flags = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0)
        if not allowed_flags:
            return
        self.refresh_from_db()
        if self.count > allowed_flags:
            self.state = self.FLAGGED
            self.save()
        else:
            self.state = self.UNFLAGGED
            self.save()


class FlagInstance(models.Model):

    flag = models.ForeignKey(Flag, on_delete=models.CASCADE, related_name='flags')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flags')
    info = models.TextField(null=True, blank=True)
    date_flagged = models.DateTimeField(auto_now=timezone.now())

    objects = FlagInstanceManager()
    reason = models.SmallIntegerField(choices=objects.REASONS, default=objects.reason_values[0])

    class Meta:
        unique_together = ('flag', 'user')
        ordering = ('date_flagged',)


@receiver(post_save, sender=FlagInstance)
def increase_count(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        instance.flag.increase_count()
        instance.flag.toggle_flagged_state()


@receiver(post_delete, sender=FlagInstance)
def decrease_count(sender, instance, using, **kwargs):
    """Decrease flag count in the flag model before deleting an instance"""
    instance.flag.decrease_count()
    instance.flag.toggle_flagged_state()


@receiver(post_save, sender=Comment)
def add_flag(sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        Flag.objects.create(comment=instance)
