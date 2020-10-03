Web API
=======

django-comments-dab uses django-rest-framework to expose a Web API that provides
developers with access to the same functionality offered through the web user interface.

The available actions with permitted user as follows:

    1. Post a new comment. (authenticated and anonymous users)

    2. Reply to an existing comment. (authenticated and anonymous users)

    3. Edit a comment. (authenticated user `comment owner`)

    4. Delete a comment you posted. (authenticated user `comment owner` and admins)

    5. React to a comment. (authenticated users)

    6. Report a comment. (authenticated users) Flagging system should be enabled.

    7. Delete flagged comment. (admins and moderators)

    8. Resolve or reject flag. This is used to revoke the flagged comment state (admins and moderators)

    9. Retrieve a list of comments and associated replies to a given content type and object ID.

    10. Confirm comment made by an anonymous users.

    11. Subscribe a thread. (authenticated users)

    12. Retrieve a list of subscribers to a given thread/content type. (admins and moderators)

These actions are explained below.

Setup:
------

To integrate the comment API in your content type (e.g Post model), in ``serializers.py``
for the Post model add comments field as shown below:


.. code:: python

    from rest_framework import serializers
    from comment.models import Comment
    from comment.api.serializers import CommentSerializer


    class PostSerializer(serializers.ModelSerializer):

        comments = serializers.SerializerMethodField()

        class Meta:
            model = Post
            fields = (
                'id',
                ...
                ...
                'comments'
            )

        def get_comments(self, obj):
            comments_qs = Comment.objects.filter_parents_by_object(obj)
            return CommentSerializer(comments_qs, many=True).data


By default all fields in profile model will be nested inside the user object in JSON response.
This can only happen if the profile attributes are defined in your ``settings.py``.
In case you would like to serialize particular fields in the profile model you should explicitly
declare the ``COMMENT_PROFILE_API_FIELDS`` tuple inside your ``settings.py``:


.. code:: python

        PROFILE_APP_NAME = 'accounts'
        PROFILE_MODEL_NAME = 'userprofile'
        # the field names below must be similar to your profile model fields
        COMMENT_PROFILE_API_FIELDS = ('display_name', 'birth_date', 'image')


Comment API actions:
--------------------

**1- Retrieve the list of comments and associated replies to a given content type and object ID:**

This action can be performed by providing the url with data queries related to the content type.

Get request accepts 3 params:


- ``model_name``: the model name of the content type that has comments associated with it.
- ``model_id``: the id of an object of that model.
- ``app_name``: the name of the app that contains the model.


Endpoint call:

::

    $ curl -H "Content-Type: application/json" '$BASE_URL/api/comments/?model_name=MODEL_NAME&model_id=ID&app_name=APP_NAME''


**2- Create a comment or reply to an existing comment:**

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

- ``type``: is the model name of the content type that have comments associated with it.
- ``id``: is the id of an object of that model
- ``parent_id``: is 0 or **NOT PROVIDED** for parent comments and for reply comments must be the id of parent comment


Example: posting a parent comment

::

    $ curl -X POST -u USERNAME:PASSWORD -d "content=CONTENT" -H "Content-Type: application/json" "$BASE_URL/api/comments/create/?model_name=MODEL_NAME&model_id=ID&app_name=APP_NAME&parent_id=0"

PS: The parent_id param can be ignored as well to post a parent comment.


**3- Update a comment:**

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

This action requires the ``comment.id`` that you want to update:


::

    $ curl -X PUT -u USERNAME:PASSWORD -d "content=CONTENT" -H "Content-Type: application/json" "$BASE_URL/api/comments/ID/


**4- Delete a comment:**

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

This action requires the ``comment.id`` that you want to delete:

::

    $ curl -X DELETE -u USERNAME:PASSWORD -H "Content-Type: application/json" "$BASE_URL/api/comments/ID/


**5- React to a comment:**

``POST`` is the allowed method to perform a reaction on a comment.

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

This action requires the ``comment.id``. and,
``reaction_type``: one of ``like`` or ``dislike``

::

   $ curl -X POST -u USERNAME:PASSWORD -H "Content-Type: application/json" "$BASE_URL/api/comments/ID/react/REACTION_TYPE/



PS: This endpoint is for toggling the reaction as in the UI, clicking the **liked** button will remove the reaction => unlike the comment. This behaviour is performed when repeating the same post request.


**6- Report a comment**

Flagging system must be enabled by adding the attribute ``COMMENT_FLAGS_ALLOWED`` to a number(other than zero e.g. 10) in ``settings.py``.

``POST`` is the allowed method to report a comment.

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

This action requires the ``comment.id``.

1. Set a flag:

.. code:: python

    payload = {
        'reason': REASON,  # number of the reason
        'info': ''  # this is required if the reason is 100 ``Something else``
    }

::

   $ curl -X POST -u USERNAME:PASSWORD -H "Content-Type: application/json" -d '{"reason":1, "info":""}' $BASE_URL/api/comments/ID/flag/


2. Un-flag a comment:

To un-flag a FLAGGED comment, set reason value to `0` or remove the payload from the request.

::

    $ curl -X POST -u USERNAME:PASSWORD $BASE_URL/api/comments/ID/flag/


**7- Change flagged comment state**

``POST`` is the allowed method to report a comment.

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

This action requires comment `admin` or `moderator` privilege.

.. code:: python

    payload = {
        'state': 3  # accepted state is 3 (REJECTED) or 4 (RESOLVED) only
    }

::

   $ curl -X POST -u USERNAME:PASSWORD -H "Content-Type: application/json" -d '{"state":3}' $BASE_URL/api/comments/ID/flag/state/change/

Repeating the same request and payload toggle the state to its original.

**8- Confirm comment made by an anonymous users**

``GET`` is the allowed method to confirm an anonymous comment.

Get request accepts 3 params:


- ``key``: is the encrypted key that contains the comment.

Example:

:: code:: bash
    $ curl -X GET -H "Content-Type: application/json" $BASE_URL/api/comments/confirm/KEY/

Since the key generated for each comment is unique, it can only be used once to verify. Any tampering with the key will result in a BAD HTTP request(400).


**9- Subscribe a thread**

``POST`` is the allowed method to toggle subscription.

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

Subscription variable ``COMMENT_ALLOW_SUBSCRIPTION`` must be enabled in ``settings.py``.

:: code:: bash
    $ curl -X POST -u USERNAME:PASSWORD -H "Content-Type: application/json" "$BASE_URL/api/comments/toggle-subscription/?model_name=MODEL_NAME&model_id=ID&app_name=APP_NAME"


**10- Retrieve subscribers on a given thread/content type**

``GET``.

Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

This action requires comment `admin` or `moderator` privilege.

:: code:: bash
    $ curl -X GET -u USERNAME:PASSWORD -H "Content-Type: application/json" $BASE_URL/api/comments/subscribers/
