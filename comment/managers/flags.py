from collections import namedtuple

from django.db import models, IntegrityError
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _


class FlagManager(models.Manager):
    def get_for_comment(self, comment):
        try:
            flag = comment.flag
        except ObjectDoesNotExist:
            flag = self.create(comment=comment)
        return flag


class FlagInstanceManager(models.Manager):

    REASONS = getattr(settings, 'COMMENT_FLAG_REASONS', [
        (1, _('Spam | Exists only to promote a service')),
        (2, _('Abusive | Intended at promoting hatred')),
    ])
    REASONS.append((100, _('Something else')))

    Reason = namedtuple('Reason', ['value', 'reason'])
    reasons_list = []
    for res in REASONS:
        reasons_list.append(Reason(*res))

    reason_values = [reason.value for reason in reasons_list]

    def _clean_reason(self, reason):
        err = ValidationError(
                _('%(reason)s is an invalid reason'),
                params={'reason': reason},
                code='invalid'
                )
        try:
            reason = int(reason)
            if reason in self.reason_values:
                return reason
            raise err

        except (ValueError, TypeError):
            raise err

    def _clean(self, reason, info):
        cleaned_reason = self._clean_reason(reason)
        cleaned_info = None

        if cleaned_reason == self.reason_values[-1]:
            cleaned_info = info
            if not cleaned_info:
                raise ValidationError(
                    _('Please supply some information as the reason for flagging'),
                    params={'info': info},
                    code='required'
                )
        return cleaned_reason, cleaned_info

    def create_flag(self, user, flag, reason, info):
        err = ValidationError(
            _('This comment is already flagged by this user (%(user)s)'),
            params={'user': user},
            code='invalid'
        )
        cleaned_reason, cleaned_info = self._clean(reason, info)
        try:
            self.create(flag=flag, user=user, reason=cleaned_reason, info=cleaned_info)
        except IntegrityError:
            raise err

    def delete_flag(self, user, flag):
        err = ValidationError(
            _('This comment was not flagged by this user (%(user)s)'),
            params={'user': user},
            code='invalid'
        )
        try:
            self.get(user=user, flag=flag).delete()
        except self.model.DoesNotExist:
            raise err

    def set_flag(self, user, flag, **kwargs):
        reason = kwargs.get('reason', None)
        info = kwargs.get('info', None)
        if reason:
            self.create_flag(user, flag, reason, info)
            created = True
        else:
            self.delete_flag(user, flag)
            created = False

        return created
