Usage
=====

1. Basics usage:
----------------

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
------------------

1. Pagination:
^^^^^^^^^^^^^^^

    By default the comments will be paginated, 10 comments per page.
    To disabled the pagination pass ``comments_per_page=None``
    To change the default number, pass ``comments_per_page=number`` to ``render_comments``.

    .. code:: html

        {% load comment_tags %}  <!-- Loading the template tag -->

        {% render_comments obj request comments_per_page=5 %}  <!-- Include all the comments belonging to a certain object -->
        {% include_bootstrap %} <!-- Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project -->
        {% include_static %} <!-- Include jQuery 3.2.1 and required js file -->



2. Integrate user profile:
^^^^^^^^^^^^^^^^^^^^^^^^^^

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

.. _Enable Flagging:

3. Enable flagging:
^^^^^^^^^^^^^^^^^^^

    The comment can be reported by the users.
    This feature can be enabled by adding the ``COMMENT_FLAGS_ALLOWED`` to ``settings.py`` and its value must be greater than 0 (the default).

    The comment that has been reported more than the ``COMMENT_FLAGS_ALLOWED`` value, will be hidden from the view.

    The default report reasons are:

        1. Spam | Exists only to promote a service.
        2. Abusive | Intended at promoting hatred.
        3. Something else. With a message info, this option will be always appended reasons list.

    The reasons can be customized by adding ``COMMENT_FLAG_REASONS`` list of tuples to ``settings.py``. E.g.

    ``settings.py``

    .. code:: python

        COMMENT_FLAG_REASONS = [
            (1, _('Spam | Exists only to promote a service')),
            (2, _('Abusive | Intended at promoting hatred')),
            (3, _('Racist | Sick mentality')),
            (4, _('Whatever | Your reason')),
            ...
        ]


