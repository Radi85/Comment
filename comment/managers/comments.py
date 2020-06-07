from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class CommentManager(models.Manager):

    def all_comments(self):
        """Filter out comments that have been flagged"""
        allowed_flags = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0)
        if not allowed_flags:
            return super().get_queryset()

        return super().get_queryset().select_related('flag').annotate(
            flags=models.F('flag__count')).filter(flags__lte=allowed_flags)

    def all_parents(self):
        return self.all_comments().filter(parent=None)

    def all_comments_by_objects(self, obj):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        return self.all_comments().filter(content_type=content_type, object_id=obj.id)

    def filter_parents_by_object(self, obj):
        return self.all_comments_by_objects(obj).filter(parent=None)

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
