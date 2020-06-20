from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models


class CommentManager(models.Manager):

    def all_exclude_flagged(self):
        """Filter out comments that have been flagged"""
        allowed_flags = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0)
        show_flagged = getattr(settings, 'COMMENT_SHOW_FLAGGED', False)
        if not allowed_flags or show_flagged:
            return super().get_queryset()

        return super().get_queryset().exclude(flag__state__exact=2)

    def all_parents(self):
        return self.all_exclude_flagged().filter(parent=None)

    def all_comments_by_object(self, obj, include_flagged=False):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        if include_flagged:
            return self.filter(content_type=content_type, object_id=obj.id)
        return self.all_exclude_flagged().filter(content_type=content_type, object_id=obj.id)

    def filter_parents_by_object(self, obj, include_flagged=False):
        if include_flagged:
            return self.all_comments_by_object(obj, include_flagged=True).filter(parent=None)
        return self.all_comments_by_object(obj).filter(parent=None)

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
