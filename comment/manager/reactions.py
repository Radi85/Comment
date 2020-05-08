"""Manager for Reaction Model"""
from django.db import models

class ReactionManager(models.Manager):
    """
    Manager to optimize SQL queries for reactions.
    """

    def get_queryset(self):
        return super().get_queryset().select_related('comment')