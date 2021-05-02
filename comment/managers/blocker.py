from django.db import models

from comment.conf import settings


class BlockedUserManager(models.Manager):
    def is_user_blocked(self, user_id=None, email=None):
        if not settings.COMMENT_ALLOW_BLOCKING_USERS:
            return False
        if user_id:
            return self._is_user_blocked_by_id(user_id)
        elif email:
            return self._is_user_blocked_by_email(email)
        return False

    def _is_user_blocked_by_id(self, user_id):
        try:
            return self.filter(user_id=int(user_id), blocked=True).exists()
        except (ValueError, TypeError):
            return False

    def _is_user_blocked_by_email(self, email):
        if not email:
            return False
        return self.filter(email=email, blocked=True).exists()

    def get_or_create_blocked_user_for_comment(self, comment):
        user_id = comment.user.id if comment.user else None
        if user_id:
            return self._get_or_create_blocked_user_by_user_id(user_id)
        return self._get_or_create_blocked_user_by_email(comment.email)

    def _get_or_create_blocked_user_by_user_id(self, user_id):
        return self.get_or_create(user_id=user_id)

    def _get_or_create_blocked_user_by_email(self, email):
        try:
            return self.get_or_create(email=email)
        except self.model.MultipleObjectsReturned:
            return self.filter(email=email, user=None).first(), False


class BlockedUserHistoryManager(models.Manager):
    def create_history(self, blocked_user, blocker, reason=None):
        self.create(
            blocked_user=blocked_user,
            blocker=blocker,
            reason=reason,
            state=int(blocked_user.blocked)
        )
