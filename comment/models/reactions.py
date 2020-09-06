from enum import IntEnum, unique

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from comment.models import Comment
from comment.managers import ReactionManager, ReactionInstanceManager


class Reaction(models.Model):
    comment = models.OneToOneField(Comment, on_delete=models.CASCADE)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)

    objects = ReactionManager()

    def _increase_count(self, field):
        self.refresh_from_db()
        setattr(self, field, models.F(field) + 1)
        self.save(update_fields=[field])

    def _decrease_count(self, field):
        self.refresh_from_db()
        setattr(self, field, models.F(field) - 1)
        self.save(update_fields=[field])

    def increase_reaction_count(self, reaction):
        if reaction == ReactionInstance.ReactionType.LIKE.value:
            self._increase_count('likes')
        else:
            self._increase_count('dislikes')

    def decrease_reaction_count(self, reaction):
        if reaction == ReactionInstance.ReactionType.LIKE.value:
            self._decrease_count('likes')
        else:
            self._decrease_count('dislikes')


class ReactionInstance(models.Model):

    @unique
    class ReactionType(IntEnum):
        LIKE = 1
        DISLIKE = 2
    CHOICES = [(r.value, r.name) for r in ReactionType]

    reaction = models.ForeignKey(Reaction, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), related_name='reactions', on_delete=models.CASCADE)
    reaction_type = models.SmallIntegerField(choices=CHOICES)
    date_reacted = models.DateTimeField(auto_now=timezone.now())

    objects = ReactionInstanceManager()

    class Meta:
        unique_together = ['user', 'reaction']
