from django.db import models


class BlockedUserManager(models.Manager):
    def is_user_blocked(self, user_id=None, email=None):
        try:
            user_id = int(user_id)
            return self.filter(user_id=user_id, blocked=True).exists()
        except (ValueError, TypeError):
            if not email:
                return False
            return self.filter(email=email, blocked=True).exists()

    def get_or_create_blocked_user_by_user_id(self, user_id):
        return self.get_or_create(user_id=user_id)

    def get_or_create_blocked_user_by_email(self, email):
        try:
            return self.get_or_create(email=email)
        except self.model.MultipleObjectsReturned:
            return self.filter(email=email, user=None).first(), False
