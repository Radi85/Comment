from collections import namedtuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from comment.models import Comment

User = get_user_model()

class Flag(models.Model):

    STATES = getattr(settings, 'COMMENT_FLAG_STATES', [
        (1, _('flagged')),
        (2, _('flag rejected by moderator')),
        (3, _('creator notified')),
        (4, _('content removed by creator')),
        (5, _('content removed by owner'))
    ])

    # Make a named tuple
    State = namedtuple('State', ['value', 'state'])

    # Construct the list of named tuples(can't use list comprehension, scope issues)
    states = []
    for state in STATES:
        states.append(State(*state))

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    count = models.PositiveIntegerField(default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flag_owners')
    state = models.SmallIntegerField(choices=STATES, default=states[0].value)
    moderator = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='flag_moderators')

    def increase_count(self):
        """Increase flag count and save the model """
        self.refresh_from_db()
        self.count = models.F('count') + 1
        self.save()

    def decrease_count(self):
        """Decrease flag count and save the model """
        self.refresh_from_db()
        if self.count > 0:
            self.count = models.F('flag') - 1
            self.save()


class FlagInstance(models.Model):
    
    REASONS = getattr(settings, 'COMMENT_FLAG_REASONS', [
        (1, _('Spam | Exists only to promote a service')),
        (2, _('Abusive | Intended at promoting hatred')),
    ])
    # add something else to the list
    REASONS.append((100, _('Something else')))

    # Make a named tuple
    Reason = namedtuple('Reason', ['value', 'reason'])

    # Construct the list of named tuples
    reasons = []
    for reason in REASONS:
        reasons.append(Reason(*reason))
    
    reason_values = [reason.value for reason in reasons]

    flag = models.ForeignKey(Flag, on_delete=models.CASCADE, related_name='flags')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flags')
    reason = models.SmallIntegerField(choices=REASONS, default=reason_values[0])
    info = models.TextField(null=True, blank=False)
    date_flagged = models.DateTimeField(auto_now=timezone.now())

    class Meta:
        unique_together = ('flag', 'user')
        ordering = ('date_flagged',)

    def clean_reason(self, reason):
        """
        Check if the reaction is a valid one or not

        Args:
            reason (int): The reason to be associated with the instance

        Raises:
            ValidationError: when reason is not a int or an unexpected reason.

        Returns:
            int: The integral value that matches to the reason value in
                the database
        """
        if isinstance(reason, int):
            if reason in self.reason_values:
                return reason

        raise ValidationError(
            _('%(reason)s is an invalid reaction'),
            code='invalid',
            params={'reason': reason}
            )

    def clean(self):
        """If something else is choosen as a reason, info shouldn't be empty"""
        reason = self.clean_reason(self.reason)
        if reason == self.reason_values[-1] and (not self.info):
            raise ValidationError(
            _('Please supply some information as the reason for flagging'),
            code='invalid'
            )

    def save(self, *args, **kwargs):
        """Increase reaction count in the reaction model after saving an instance"""
        self.clean()
        super().save(*args, **kwargs)
        self.flag.increase_count()

    def set_flag(self, user, reason, info=None):
        """
        Add/remove a flag instance

        Args:
            user (`get_user_model()`): user.
            reason (int): the reason that needs to be added.
            info (str): any additional info that needs to be associated to the model.

        Returns:
            bool: True if created, False if deleted.
        """
        reason = self.clean_reason(reason=reason)
        flag_obj = self.flag

        try:
            created = False
            instance = FlagInstance.objects.get(flag=flag_obj, user=user)
            instance.delete()
        except models.ObjectDoesNotExist:
            instance = FlagInstance.objects.create(
                flag=flag_obj,
                user=user,
                reason=reason,
                info=info
            )
            created = True

        return created


@receiver(post_delete, sender=FlagInstance)
def delete_flag_instance(sender, instance, using, **kwargs):
    """Decrease flag count in the flag model before deleting an instance"""
    instance.decrease_count()

    

