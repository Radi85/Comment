Setup
-----

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

``get_comments`` *tag uses 2 positional and 3 optional args*:

    1. The instance of the model. (**positional**)
    2. Request object. (**positional**)
    3. oauth. (optional - Default is false)
    4. paginate. (optional - Default is false)
    5. cpp (number of Comments Per Page - Default is 10)


1. Basic usage:
^^^^^^^^^^^^^^^

``include_static`` this tag will include required jquery and javascript
file. ``include_bootstrap`` for bootstrap 4.1.1 if it’s already included
in your project, get rid of this tag.

In your template (e.g. post-detail.html) add the following template tags
where object is the instance of post.

.. code:: python

    {% load comment_tags %}  # Loading the template tag
    {% get_comments object request %}  # Include all the comments belonging to a certain object
    {% include_bootstrap %} # Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project
    {% include_static %} # Include jQuery 3.2.1 and required js file



2. Advanced usage:
^^^^^^^^^^^^^^^^^^

    **1. Add pagination:**

    To add pagination to your comments, you need to pass two variables to the ``get_comments`` tag.
    ``paginate`` must be set to ``True`` and set ``cpp`` var (number of comments per page - default is 10) to the desired number of comments per page.
    e.g. If you would like to have 5 comments per page, the ``get_comments`` tag should look like this:

    .. code:: python

        {% load comment_tags %}  # Loading the template tag
        {% get_comments object request paginate=True cpp=5 %}  # Include all the comments belonging to a certain object
        {% include_bootstrap %} # Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project
        {% include_static %} # Include jQuery 3.2.1 and required js file
        



    **2. Integrate existing profile app with comments app:**

    If you have profile model for the user and you would like to show the
    profile image on each comment you need to assign PROFILE_APP_NAME and
    PROFILE_MODEL_NAME variables in your ``settings.py`` file. (e.g if user profile
    app is called ``accounts`` and profile model is called ``UserProfile``)
    Update your ``settings.py``:

    .. code:: python

        PROFILE_APP_NAME = 'accounts'
        PROFILE_MODEL_NAME = 'UserProfile' # letter case insensitive
