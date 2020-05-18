from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

ALLOWED_FLAGS = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 10)

class CommentManager(models.Manager):
    def get_queryset(self):
        """Filter out comments that have been flagged"""
        return super().get_queryset().annotate(
            flag_count=models.Count('flags')).filter(flag_count__gt=ALLOWED_FLAGS)

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
