from django.contrib.auth import get_user_model
from django.db import models

from comment.messages import BlockState
from comment.managers import BlockedUserManager, BlockedUserHistoryManager


class BlockedUser(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    blocked = models.BooleanField(default=True)

    objects = BlockedUserManager()

    def __str__(self):
        return getattr(self.user, self.user.USERNAME_FIELD) if self.user else self.email


class BlockedUserHistory(models.Model):
    UNBLOCKED = 0
    BLOCKED = 1
    STATES_CHOICES = [
        (UNBLOCKED, BlockState.UNBLOCKED),
        (BLOCKED, BlockState.BLOCKED),
    ]
    blocked_user = models.ForeignKey(BlockedUser, on_delete=models.CASCADE)
    blocker = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    state = models.SmallIntegerField(choices=STATES_CHOICES, default=BLOCKED)
    date = models.DateTimeField(auto_now_add=True)

    objects = BlockedUserHistoryManager()
