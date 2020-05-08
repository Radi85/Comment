from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

from comment.manager.comments import CommentManager

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

    class Meta:
        ordering = ['-posted', ]

    def __str__(self):
        if not self.parent:
            return f'comment by {self.user}: {self.content[:20]}'
        else:
            return f'reply by {self.user}: {self.content[:20]}'

    def __repr__(self):
        return self.__str__()

    @property
    def replies(self):
        return Comment.objects.filter(parent=self).order_by('posted')
