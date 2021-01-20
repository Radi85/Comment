from django.contrib.contenttypes.models import ContentType
from django.db import models

from comment.conf import settings
from comment.utils import id_generator
from comment.validators import _validate_order


class CommentManager(models.Manager):

    def all_exclude_flagged(self):
        """Filter out comments that have been flagged"""
        allowed_flags = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0)
        show_flagged = getattr(settings, 'COMMENT_SHOW_FLAGGED', False)
        if not allowed_flags or show_flagged:
            return super().get_queryset()

        return super().get_queryset().exclude(flag__state__exact=2)

    @staticmethod
    def _filter_parents(qs, parent=None):
        return qs.filter(parent=parent).order_by(*_validate_order())

    def all_parents(self):
        qs = self.all_exclude_flagged()
        return self._filter_parents(qs)

    def all_comments_by_object(self, obj, include_flagged=False):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        if include_flagged:
            return self.filter(content_type=content_type, object_id=obj.id)
        return self.all_exclude_flagged().filter(content_type=content_type, object_id=obj.id)

    def filter_parents_by_object(self, obj, include_flagged=False):
        if include_flagged:
            qs = self.all_comments_by_object(obj, include_flagged=True)
        else:
            qs = self.all_comments_by_object(obj)

        return self._filter_parents(qs)

    @staticmethod
    def generate_urlhash():
        return id_generator(
            prefix=settings.COMMENT_URL_PREFIX,
            len_id=settings.COMMENT_URL_ID_LENGTH,
            suffix=settings.COMMENT_URL_SUFFIX
            )

    def get_parent_comment(self, parent_id):
        parent_comment = None
        if parent_id or parent_id == '0':
            parent_qs = self.filter(id=parent_id)
            if parent_qs.exists():
                parent_comment = parent_qs.first()
        return parent_comment

    def comment_exists(self, comment):
        return self.model.objects.filter(email=comment.email, posted=comment.posted).count() > 0
