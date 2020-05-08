Setup
=====

Step 1 - Connecting comment model with the target model:
--------------------------------------------------------

In your models.py add the field ``comments`` as a ``GenericRelation`` field to the required model.

PS: Please note that field name must be ``comments`` **NOT** ``comment``.

E.g. ``Post`` model, as shown below:

.. code:: python

    from django.contrib.contenttypes.fields import GenericRelation
    from comment.models import Comment

    class Post(models.Model):
        author = models.ForeignKey(User)
        title = models.CharField(max_length=200)
        body = models.TextField()
        # the field name should be comments
        comments = GenericRelation(Comment)

Step 2 - Adding template tags:
------------------------------

``render_comments`` *tag uses 2 positional and 2 optional args*:

    1. Instance of the targeted model. (**positional**)
    2. Request object. (**positional**)
    3. oauth. (optional - Default is false)
    4. comments_per_page (number of Comments Per Page - Default is 10)

