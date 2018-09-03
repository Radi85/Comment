Setup
=====

Step 1
~~~~~~

In your models.py add the field comments (Please note that field name
must be ``comments`` not ``comment``) to the model for which comment
should be added (e.g. Post) and the appropriate imports as shown below:

.. code:: python

    from django.contrib.contenttypes.fields import GenericRelation
    from comment.models import Comment

    class Post(models.Model):
        author = models.ForeignKey(User)
        title = models.CharField(max_length=200)
        body = models.TextField()
        # the field name should be comments
        comments = GenericRelation(Comment)



Step 2
~~~~~~

``get_comments`` *tag uses 2 positional and 1 optional args*:

    1. The instance of the model. (positional)
    2. User instance. (positional)
    3. oauth. (optional - Default is false)


``include_static`` this tag will include required jquery and javascript
file. ``include_bootstrap`` for bootstrap 4.1.1 if it’s already included
in your project, get rid of this tag.

In your template (e.g. post-detail.html) add the following template tags
where object is the instance of post.

.. code:: python

    {% load comment_tags %}  # Loading the template tag
    {% get_comments object request.user %}  # Include all the comments belonging to a certain object
    {% include_bootstrap %} # Include bootstrap 4.1.1
    {% include_static %} # Include jQuery 3.2.1 and required js file


Integrate existing profile app with comments app
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have profile model for the user and you would like to show the
profile image on each comment you need to assign PROFILE_APP_NAME and
PROFILE_MODEL_NAME variables in your ``settings.py`` file. (e.g if user profile
app is called ``accounts`` and profile model is called ``UserProfile``)
Update your ``settings.py``:

.. code:: python

    PROFILE_APP_NAME = 'accounts'
    PROFILE_MODEL_NAME = 'UserProfile' # letter case insensitive

--------------
