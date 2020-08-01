from django.db import models
from django.urls import reverse
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation

from comment.models import Comment


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    title = models.CharField(max_length=150)
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    editdate = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True)
    # comment app
    comments = GenericRelation(Comment)

    class Meta:
        ordering = ['-editdate', '-date']

    def get_absolute_url(self):
        return reverse('post:postdetail', kwargs={'slug': self.slug})

    def __str__(self):
        return f"By {self.author}: {self.title[:25]}"

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            _title = self.title
            if len(_title) > 45:
                _title = _title[:45]
            unique_slug = self.slug = slugify(_title)
            count = 1
            while self.__class__.objects.filter(slug=unique_slug).exists():
                unique_slug = "{0}-{1}".format(self.slug, count)
                count += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
