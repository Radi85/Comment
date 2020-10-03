Usage
=====

1. Basics usage:
----------------

Rendering Comments
^^^^^^^^^^^^^^^^^^

``include_bootstrap`` tag is for bootstrap-4.1.1, if it’s already used in the project, get rid of this tag.

In the template (e.g. post_detail.) add the following template tags where ``obj`` is the instance of post model.

.. code:: jinja

    {% load comment_tags %}  {# Loading the template tag #}
    {% render_comments obj request %}  {# Render all the comments belong to the passed object "obj" #}
    {% include_bootstrap %} {# Include bootstrap 4.1.1 - remove this line if BS is already used in your project #}


Display Comment Count
^^^^^^^^^^^^^^^^^^^^^

In a template where you may want to display count, the following tag can be used.

.. code:: jinja

    {% get_comments_count obj user %}

Here, ``obj`` refers to the post object instance


2. Advanced usage:
------------------

1. Pagination:
^^^^^^^^^^^^^^^

By default, the comments will be paginated, 10 comments per page.
To disable the pagination, set ``COMMENT_PER_PAGE=None`` in your settings file.
To change the default number, set ``COMMENT_PER_PAGE=number``.

.. code:: jinja

    {% load comment_tags %}  {# Loading the template tag #}

    {% render_comments obj request %}  {# Include comments belonging to a certain object #}
    {% include_bootstrap %} {# Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project #}


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


4. Allow commenting by anonymous:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Commenting by anonymous is disabled by default.
After enabling this feature, unauthenticated users will be able to post a comment by providing their email address. An email will be sent to confirmation. Only after confirming their email address, the comment will be saved in the DB associated with the anonymous user's email.
comment only hits the database, after it is verified.

However, since these comment are created anonymously, they won't be editable nor deletable like a normal comments(``comment_admins`` and ``comment_moderators`` can still delete them).

Before enabling this feature, make sure you set the ``get_absolute_url`` method on the model object with which the Comment model has been associated.
For e.g, if the ``Comment`` model has been associated with the ``Post`` model, make sure you have something like this set inside your ``models.py``

.. code:: python

    class Post(models.Model):
    ...
    slug = models.SlugField(unique=True)
    ...

    def get_absolute_url(self):
        return reverse('post:postdetail', kwargs={'slug': self.slug})


To enable this feature, the following settings variables need to be set alongside with django email settings:

.. code:: python

    COMMENT_ALLOW_ANONYMOUS = True
    COMMENT_FROM_EMAIL = 'no-reply@email.com'   # used for sending confirmation emails, if not set `EMAIL_HOST_USER` will be used.

Also, related to sending of email the following settings need to set.

.. code:: python

    EMAIL_HOST_USER = 'user@domain'
    EMAIL_HOST_PASSWORD = 'password'
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'    # this backend won't send emails but will just print them to the console. For production use your own backend.

    # e.g for if you are using gmail address, you may set:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'

To further customize different attributes related to anonymous commenting, you may look into the `Settings`_ section for different configurations.

.. _`Settings`: https://django-comment-dab.readthedocs.io/settings.html/


5. Enable gravatar:
^^^^^^^^^^^^^^^^^^^^

To enable using gravatar for profile pics set ``COMMENT_USE_GRAVATAR`` in `settings.py` to ``True``


6. Enable subscription:
^^^^^^^^^^^^^^^^^^^^^^^^

To enable app subscription set ``COMMENT_ALLOW_SUBSCRIPTION`` in `settings.py` to ``True``

This will enable the UI functionality and the API endpoint to follow and unfollow `thread`.

The thread can be a `parent` comment or the `content type` (i.g. Post, Picture, Video...) that uses the comment model.

**Automatic Subscription:**

    1. Creating a comment in a thread will set the user automatically as a follower of the `thread`.
    2. Replying to a comment will set the user as a follower of the `parent` comment

An email notification will be sent to the thread's followers up on adding a new comment to the thread.

PS: This feature needs the email settings to be configured similar to `4. Allow commenting by anonymous:`_
