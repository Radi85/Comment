Settings
=========

django-comments-dab has a few configuration options that allow you to customize it.

PROFILE_APP_NAME
^^^^^^^^^^^^^^^^

The django app that contains the model that has user profiles. This will be used to display profile pictures alongside the comments. Defaults to ``None``.


PROFILE_MODEL_NAME
^^^^^^^^^^^^^^^^^^

The model that contains the user profiles. This will be used in display profile pictures alongside the comments. Defaults to ``None``.


COMMENT_PROFILE_API_FIELDS
^^^^^^^^^^^^^^^^^^^^^^^^^^

This will only be useful if ``PROFILE_APP_NAME`` and ``PROFILE_MODEL_NAME`` are defined in your ``settings.py``.
By default all fields in profile model will be nested inside the user object in JSON response.
In case you would like to serialize particular fields in the profile model you should explicitly
declare the ``COMMENT_PROFILE_API_FIELDS`` tuple inside your ``settings.py``:


.. code:: python

        PROFILE_APP_NAME = 'accounts'
        PROFILE_MODEL_NAME = 'userprofile'
        # the field names below must be similar to your profile model fields
        COMMENT_PROFILE_API_FIELDS = ('display_name', 'birth_date', 'image')


COMMENT_USER_API_FIELDS
^^^^^^^^^^^^^^^^^^^^^^^^

The fields returned for the ``user`` serializer by the REST API. Defaults to ``['id', 'username', 'email']``.

COMMENT_FLAGS_ALLOWED
^^^^^^^^^^^^^^^^^^^^^^

Number of flags allowed before a comment is termed as flagged for review. Defaults to ``10``. To disable the flagging feature set this as ``None`` or ``0``.


COMMENT_SHOW_FLAGGED
^^^^^^^^^^^^^^^^^^^^^

Should flagged comment be shown or not? Defaults to ``False``.


COMMENT_FLAG_REASONS
^^^^^^^^^^^^^^^^^^^^^

The reasons for which a comment can be flagged. Users will have a choose one of these before they flag a comment. This a list of tuples. Defaults to:

.. code:: python

    from django.utils.translation import gettext_lazy as _

    [
        (1, _('Spam | Exists only to promote a service')),
        (2, _('Abusive | Intended at promoting hatred')),
    ]


COMMENT_URL_PREFIX
^^^^^^^^^^^^^^^^^^^

The prefix to be used when assigning a ``urlhash`` to a comment. Defaults to ``'comment-'``.


COMMENT_URL_SUFFIX
^^^^^^^^^^^^^^^^^^^

The prefix to be used when assigning a ``urlhash`` to a comment. Defaults to ``''``.


COMMENT_URL_ID_LENGTH
^^^^^^^^^^^^^^^^^^^^^^

The length of the unique id generated for ``urlhash`` to a comment. Defaults to ``8``.


COMMENT_PER_PAGE
^^^^^^^^^^^^^^^^^

No. of comments to be displayed per page. Defaults to ``10``. To disable pagination, set it to ``None``.


COMMENT_ORDER_BY
^^^^^^^^^^^^^^^^^
Order parent comments in a specific order. Defaults to ``['-posted']``.

.. note::
    Allowed order should contain a combination of any of the following values without repeating themselves.

+--------------------------+------------------------------------------------+
| Value                    | Comment Ordered By                             |
+==========================+================================================+
| ``posted``               | Date posted, ascendingly                       |
+--------------------------+------------------------------------------------+
| ``-posted``              | Date posted, descending                        |
+--------------------------+------------------------------------------------+
| ``reaction__likes``      | Like count, ascendingly                        |
+--------------------------+------------------------------------------------+
| ``-reaction__likes``     | Like count, descendingly                       |
+--------------------------+------------------------------------------------+
| ``reaction__dislikes``   | Dislike count, ascendingly                     |
+--------------------------+------------------------------------------------+
| ``-reaction__dislikes``  | Dislike count, descendingly                    |
+--------------------------+------------------------------------------------+
| ``?``                    | Random                                         |
+--------------------------+------------------------------------------------+


COMMENT_ALLOW_ANONYMOUS
^^^^^^^^^^^^^^^^^^^^^^^^

Should the anonymous commenting featured be allowed? Defaults to ``False``.

COMMENT_FROM_EMAIL
^^^^^^^^^^^^^^^^^^^

The email address to be used for sending email for comment confirmation. Defaults to the value of ``EMAIL_HOST_USER``.

COMMENT_CONTACT_EMAIL
^^^^^^^^^^^^^^^^^^^^^^

Used for contact address in confirmation emails. For e.g. ``contact@domain``. Defaults to the value of ``COMMENT_FROM_EMAIL``.

COMMENT_SEND_HTML_EMAIL
^^^^^^^^^^^^^^^^^^^^^^^^

Should the email to be sent for confirmation contain ``html`` part as well? Defaults to ``True``.

COMMENT_ANONYMOUS_USERNAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Username to be shown beside anonymous comment. Defaults to ``Anonymous User``.

COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Whether to use the first part of the email address as username for anonymous comments? For e.g. for ``user@domain``, ``user`` will be used. Defaults to ``False``.

COMMENT_USE_GRAVATAR
^^^^^^^^^^^^^^^^^^^^^

Whether to use gravatar_ for displaying profile pictures alongside comments. Defaults to ``False``.

.. _gravatar: https://gravatar.com/


COMMENT_ALLOW_SUBSCRIPTION
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Allow threads subscription feature. Defaults to ``False``.


COMMENT_WRAP_CONTENT_WORDS
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Number of comment content to be show and the rest of words to be wrapped.
Default is ``30``. Changing it to ``0`` or ``None`` no words will be wrapped (Full content is shown/rendered).

COMMENT_DEFAULT_PROFILE_PIC_LOC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Provides an alternate location for profile picture that can be used other than
default image. Defaults to '/static/img/default.png'
