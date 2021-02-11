from math import ceil

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils import timezone

from comment.managers import CommentManager
from comment.conf import settings
from comment.utils import is_comment_moderator


class Comment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
    email = models.EmailField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    content = models.TextField()
    urlhash = models.CharField(
        max_length=50,
        unique=True,
        editable=False
        )
    posted = models.DateTimeField(default=timezone.now, editable=False)
    edited = models.DateTimeField(auto_now=True)

    objects = CommentManager()

    class Meta:
        ordering = ['-posted', ]

    def __str__(self):
        username = self.get_username()
        _content = self.content[:20]
        if not self.parent:
            return f'comment by {username}: {_content}'
        else:
            return f'reply by {username}: {_content}'

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            'user': self.user,
            'content': self.content,
            'email': self.email,
            'posted': str(self.posted),
            'app_name': self.content_type.app_label,
            'model_name': self.content_type.model,
            'model_id': self.object_id,
            'parent': getattr(self.parent, 'id', None)
        }

    def _get_reaction_count(self, reaction_type):
        return getattr(self.reaction, reaction_type, None)

    def replies(self, include_flagged=False):
        manager = self.__class__.objects
        if include_flagged:
            qs = manager.all()
        else:
            qs = manager.all_exclude_flagged()

        return manager._filter_parents(qs, parent=self)

    def _set_unique_urlhash(self):
        if not self.urlhash:
            self.urlhash = self.__class__.objects.generate_urlhash()
            while self.__class__.objects.filter(urlhash=self.urlhash).exists():
                self.urlhash = self.__class__.objects.generate_urlhash()

    def _set_email(self):
        if self.user:
            self.email = getattr(self.user, self.user.EMAIL_FIELD, '')

    def _get_username_for_anonymous(self):
        if settings.COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME:
            return self.email.split('@')[0]

        return settings.COMMENT_ANONYMOUS_USERNAME

    def get_username(self):
        user = self.user
        if not user:
            return self._get_username_for_anonymous()

        return getattr(user, user.USERNAME_FIELD)

    def save(self, *args, **kwargs):
        self._set_unique_urlhash()
        self._set_email()
        super(Comment, self).save(*args, **kwargs)

    def get_url(self, request):
        page_url = self.content_object.get_absolute_url()
        comments_per_page = settings.COMMENT_PER_PAGE
        if comments_per_page:
            qs_all_parents = self.__class__.objects.filter_parents_by_object(
                self.content_object, include_flagged=is_comment_moderator(request.user)
                )
            position = qs_all_parents.filter(posted__gte=self.posted).count() + 1
            if position > comments_per_page:
                page_url += '?page=' + str(ceil(position / comments_per_page))
        return page_url + '#' + self.urlhash

    @property
    def is_parent(self):
        return self.parent is None

    @property
    def is_edited(self):
        if self.user:
            return self.posted.timestamp() + 1 < self.edited.timestamp()
        return False

    @property
    def likes(self):
        return self._get_reaction_count('likes')

    @property
    def dislikes(self):
        return self._get_reaction_count('dislikes')

    @property
    def is_flagged(self):
        if hasattr(self, 'flag') and self.flag.is_flag_enabled:
            return self.flag.state != self.flag.UNFLAGGED
        return False

    @property
    def has_flagged_state(self):
        if hasattr(self, 'flag'):
            return self.flag.state == self.flag.FLAGGED
        return False

    @property
    def has_rejected_state(self):
        if hasattr(self, 'flag'):
            return self.flag.state == self.flag.REJECTED
        return False

    @property
    def has_resolved_state(self):
        if hasattr(self, 'flag'):
            return self.flag.state == self.flag.RESOLVED
        return False
