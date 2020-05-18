from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

from comment.managers import CommentManager


class Comment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, default=None)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    content = models.TextField()
    posted = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)

    objects = CommentManager()

    ALLOWED_FLAGS = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 10)

    class Meta:
        ordering = ['-posted', ]

    def __str__(self):
        if not self.parent:
            return f'comment by {self.user}: {self.content[:20]}'
        else:
            return f'reply by {self.user}: {self.content[:20]}'

    def __repr__(self):
        return self.__str__()

    def _get_reaction_count(self, reaction_type):
        return getattr(self.reaction, reaction_type, None)

    @property
    def replies(self):
        return Comment.objects.filter(parent=self).order_by('posted')

    @property
    def is_parent(self):
        return self.parent is None

    @property
    def is_edited(self):
        return self.posted.timestamp() + 1 < self.edited.timestamp()

    @property
    def likes(self):
        return self._get_reaction_count('likes')

    @property
    def dislikes(self):
        return self._get_reaction_count('dislikes')

    @property
    def is_flagged(self):
        if self.flags.get(comment=self).count > self.ALLOWED_FLAGS:
            return True
        return False
