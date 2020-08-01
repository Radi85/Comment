Usage
=====

1. Basics usage:
----------------

``include_static`` this tag will include CSS and javascript files,

``include_bootstrap`` tag is for bootstrap-4.1.1, if it’s already used in the project, get rid of this tag.

In the template (e.g. post_detail.) add the following template tags where ``obj`` is the instance of post model.

.. code:: jinja

    {% load comment_tags %}  {# Loading the template tag #}
    {% render_comments obj request %}  {# Render all the comments belong to the passed object "obj" #}


2. Advanced usage:
------------------

1. Pagination:
^^^^^^^^^^^^^^^

By default, the comments will be paginated, 10 comments per page.
To disable the pagination pass ``comments_per_page=None``
To change the default number, pass ``comments_per_page=number`` to ``render_comments``.

.. code:: jinja

    {% load comment_tags %}  {# Loading the template tag #}

    {% render_comments obj request comments_per_page=0 %}  {# Include all the comments belonging to a certain object #}
    {% include_bootstrap %} {# Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project #}
    {% include_static %} {# Include comment CSS and JS files #}



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

.. _`Enable Flagging`:

3. Enable flagging:
^^^^^^^^^^^^^^^^^^^

The comment can be reported by the users.
This feature can be enabled by adding the ``COMMENT_FLAGS_ALLOWED`` to ``settings.py`` and its value must be greater than 0 (the default).

The comment that has been reported more than the ``COMMENT_FLAGS_ALLOWED`` value, will be hidden from the view.
To keep displaying the flagged comments to all users add ``COMMENT_SHOW_FLAGGED=True`` to ``settings.py``

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

The flag model has currently 4 states: `since v1.6.7`

    1. UNFLAGGED
    2. **FLAGGED** - this case only the comment will be hidden
    3. REJECTED - flag reasons are rejected by the moderator
    4. RESOLVED - the comment content has been changed and accepted by the moderator


Groups and Permissions:
"""""""""""""""""""""""
For flagging purpose, the following groups and permissions will be created on the next migrate:

**permissions:**
    1. delete_comment  (default)
    2. delete_flagged_comment

**groups:**
    1. comment_admin => has both mentioned permissions (edit permission might be added in the future)
    2. comment_moderator => has delete_flagged_comment permission

* Comment admin can delete any comment and change the state of flagged comment.
* Comment moderator can delete FLAGGED comment only and change their state.

PS: If the groups or the permissions don't exist, just run migrate. ``./manage.py migrate``
