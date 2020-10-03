from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

from comment.managers.followers import FollowerManager


class Follower(models.Model):
    email = models.EmailField()
    username = models.CharField(max_length=50)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    objects = FollowerManager()

    def __str__(self):
        return f'{str(self.content_object)} followed by {self.email}'

    def __repr__(self):
        return self.__str__()
