from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class CommentManager(models.Manager):
    def all_parent_comments(self):
        return super().all().filter(parent=None)

    def filter_parents_by_object(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        object_id = obj.id
        qs = super().filter(content_type=content_type, object_id=object_id).filter(parent=None)
        return qs

    def all_comments_by_objects(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        object_id = obj.id
        qs = super().filter(content_type=content_type, object_id=object_id)
        return qs

    def create_by_model_type(self, model_type, pk, content, user, parent_obj=None):
        model_qs = ContentType.objects.filter(model=model_type)
        if model_qs.exists():
            model_class = model_qs.first().model_class()
            obj_qs = model_class.objects.filter(id=pk)
            if obj_qs.exists() and obj_qs.count() == 1:
                instance = self.model()
                instance.content = content
                instance.user = user
                instance.content_type = model_qs.first()
                instance.object_id = obj_qs.first().id
                if parent_obj:
                    instance.parent = parent_obj
                instance.save()
                return instance
        return None


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

    @property
    def is_edited(self):
        return self.posted.timestamp() + 1 < self.edited.timestamp()
