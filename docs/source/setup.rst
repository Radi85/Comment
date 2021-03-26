Setup
=====

Step 1 - Connecting comment model with the target model
-------------------------------------------------------

In models.py add the field ``comments`` as a ``GenericRelation`` field to the required model.

PS: Please note that the field name must be ``comments`` **NOT** ``comment``.

E.g. ``Post`` model, as shown below:

.. code:: python

    from django.contrib.contenttypes.fields import GenericRelation

    from comment.models import Comment

    class Post(models.Model):
        author = models.ForeignKey(User)
        title = models.CharField(max_length=200)
        slug = models.SlugField(unique=True)
        body = models.TextField()
        # the field name should be comments
        comments = GenericRelation(Comment)

.. important::

    Please add a ``get_absolute_url`` method to the model that you're associating with the ``Comment`` model. It is used at several places.

    .. code:: python

        from django.urls import reverse

        def get_absolute_url(self):
            return reverse('post_detail_url', kwargs={'slug': self.slug})

Step 2 - Adding template tags:
------------------------------

``render_comments`` *tag uses 2 required and 1 optional arg*:

    1. Instance of the targeted model. (**Required**)
    2. Request object. (**Required**)
    3. oauth. (optional - Default is false)
