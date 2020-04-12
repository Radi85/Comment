Setup
-----

Step 1 - Connecting comment model with the target model:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``render_comments`` *tag uses 2 positional and 2 optional args*:

    1. Instance of the targeted model. (**positional**)
    2. Request object. (**positional**)
    3. oauth. (optional - Default is false)
    4. comments_per_page (number of Comments Per Page - Default is 10)


1. Basics usage:
^^^^^^^^^^^^^^^^

``include_static`` this tag will include required jquery and javascript file,
if you already use jquery please make sure it is not the slim version which doesn't support ajax.
``include_bootstrap`` tag is for bootstrap-4.1.1, if it’s already included
in your project, get rid of this tag.

In your template (e.g. post_detail.html) add the following template tags where ``obj`` is the instance of post model.

.. code:: python

    {% load comment_tags %}  # Loading the template tag
    {% render_comments obj request %}  # Render all the comments belonging to a passed object


**Include static files:**

The ``comment`` app has three template tags for static files that the app requires.
These tags need to be included in the end of your base template.


- **Case 1:** You already have jQuery in your project then the following tags shall be included below jQuery file:

.. code:: html

    {% load comment_tags %}  <!-- Loading the template tag -->

    <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
    {% include_static %}  <!-- Include comment.js file only -->
    {% include_bootstrap %}  <!-- Include bootstrap-4.1.1 - remove this line if it is already used in your project -->


- **Case 2:** You don't have jQuery in your project then the following tags shall be included:

.. code:: html

    {% load comment_tags %}  <!-- Loading the template tag -->

    {% include_static_jquery %}  <!-- Include mini jQuery 3.2.1 and required js file -->
    {% include_bootstrap %}  <!-- Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project -->


2. Advanced usage:
^^^^^^^^^^^^^^^^^^

    **1. Customize or remove the pagination:**

    By default the comments will be paginated, 10 comments per page.
    To disabled the pagination pass ``comments_per_page=None``
    To change the default number, pass ``comments_per_page=number`` to ``render_comments``.

    .. code:: html

        {% load comment_tags %}  <!-- Loading the template tag -->

        {% render_comments obj request comments_per_page=5 %}  <!-- Include all the comments belonging to a certain object -->
        {% include_bootstrap %} <!-- Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project -->
        {% include_static %} <!-- Include jQuery 3.2.1 and required js file -->



    **2. Integrate existing profile app with comments app:**

    If you have a profile model for the user and you would like to show the
    profile image next to each comment, do the following steps:

    - Add ``PROFILE_APP_NAME`` and ``PROFILE_MODEL_NAME`` variables to your ``settings.py`` file.
        e.g if user profile app is called ``accounts`` and profile model is called ``UserProfile``

        ``settings.py``:

        .. code:: python

            PROFILE_APP_NAME = 'accounts'
            PROFILE_MODEL_NAME = 'UserProfile' # letter case insensitive



    - Make sure that ``get_absolute_url`` method is defined in your profile model.

        .. code:: python

            from django.urls import reverse

            class UserProfile(models.Model):
                user = models.OneToOneField(User, on_delete=models.CASCADE)
                ...
                ...

                # this method must be defined for appropriate url mapping in comments section
                def get_absolute_url(self):
                    return reverse('your_profile_url_name')
