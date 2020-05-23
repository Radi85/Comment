from collections import namedtuple

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class FlagManager(models.Manager):

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


class FlagInstanceManager(models.Manager):

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

    def _clean_reason(self, reason):
        try:
            reason = int(reason)
            if reason in self.reason_values:
                return reason

        except (ValueError, TypeError):
            raise ValidationError(
                _('%(reason)s is an invalid reaction'),
                code='invalid',
                params={'reason': reason}
                )

    def _clean_action(self, action):
        if isinstance(action, str):
            act = action.lower()
            if act in ['create', 'delete']:
                return act

        return ValidationError(_('This is not a valid action'), code='invalid')

    def _clean(self, reason, info):
        reason = self._clean_reason(reason)
        if not reason:
            raise ValidationError(
                {'reason': _('Please supply a reason for flagging')},
                code='required'
                )

        if reason == self.reason_values[-1] and (not info):
            raise ValidationError(
                {'info': _('Please supply some information as the reason for flagging')},
                code='required'
                )

    def set_flag(self, user, flag, data):
        reason = data.get('reason', None)
        info = data.get('info', None)
        action = data.get('action', None)
        self._clean_action(action)
        if action == 'delete':
            instance = self.get(flag=flag, user=user)
            instance.delete()
            created = False
        else:
            self._clean(reason, info)
            self.create(flag=flag, user=user, reason=reason, info=info)
            created = True

        return created
