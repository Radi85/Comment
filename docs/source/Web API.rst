Web API
=======

django-comments-dab uses django-rest-framework to expose a Web API that provides
developers with access to the same functionality offered through the web user interface.

There are 5 methods available to perform the following actions:


    1. Post a new comment. (Authenticated)

    2. Reply to an existing comment. (Authenticated)

    3. Edit a comment you posted. (Authenticated)

    4. Delete a comment you posted. (Authenticated)

    5. React to a comment. (Authenticated)

    6. Report a comment. (Authenticated) Flagging system should be enabled

    7. Retrieve the list of comments and associated replies to a given content type and object ID.

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


    - ``type``: is the model name of the content type that have comments associated with it.
    - ``id``: is the id of an object of that model




    For example if you are using axios to retrieve the comment list of second object (id=2) of a model (content type) called post.
    you can do the following:

    ::

        $ curl -H "Content-Type: application/json" 'http://localhost:8000/api/comments/?type=MODEL_NAME&id=ID'


**2- Create a comment or reply to an existing comment:**

    Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

    - ``type``: is the model name of the content type that have comments associated with it.
    - ``id``: is the id of an object of that model
    - ``parent_id``: is 0 or **NOT PROVIDED** for parent comments and for reply comments must be the id of parent comment


    Example: posting a parent comment

    ::

        $ curl -X POST -u USERNAME:PASSWORD -d "content=CONTENT" -H "Content-Type: application/json" "http://localhost:8000/api/comments/create/?type=MODEL_NAME&id=ID&parent_id=0"


**3- Update a comment:**

    Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

    This action requires the ``comment.id`` that you want to update:


    ::

        $ curl -X PUT -u USERNAME:PASSWORD -d "content=CONTENT" -H "Content-Type: application/json" "http://localhost:8000/api/comments/ID/


**4- Delete a comment:**

    Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

    This action requires the ``comment.id`` that you want to delete:

    ::

        $ curl -X DELETE -u USERNAME:PASSWORD -H "Content-Type: application/json" "http://localhost:8000/api/comments/ID/


**5- React to a comment:**

    ``POST`` is the allowed method to perform a reaction on a comment.

    Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

    This action requires the ``comment.id``. and,
    ``reaction_type``: one of ``like`` or ``dislike``

    ::

       $ curl -X POST -u USERNAME:PASSWORD -H "Content-Type: application/json" "http://localhost:8000/api/comments/ID/react/REACTION_TYPE/


    PS: As in the UI, clicking the **liked** button will remove the reaction => unlike the comment. This behaviour is performed when repeating the same post request.


**6- Report a comment**

    Flagging system must be enabled by adding the attribute ``COMMENT_FLAGS_ALLOWED`` to ``settings.py``. See :ref:`Enable Flagging`.

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

       $ curl -X POST -u USERNAME:PASSWORD -H "Content-Type: application/json" -d '{"reason":1, "info":""}' http://localhost:8000/api/comments/ID/flag/


    2. Un-flag a comment:

        To un-flag a FLAGGED comment, set reason value to `0` or remove the payload from the request.

    ::

    $ curl -X POST -u USERNAME:PASSWORD http://localhost:8000/api/comments/ID/flag/


