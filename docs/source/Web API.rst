
Web API
-------

django-comments-dab uses django-rest-framework to expose a Web API that provides
developers with access to the same functionalities offered through the web user interface.

There are 5 methods available to perform the following actions:


    1. Post a new comment. (Authenticated)

    2. Reply to an existing comment. (Authenticated)

    3. Edit a comment you posted. (Authenticated)

    4. Delete a comment you posted. (Authenticated)

    5. Retrieve the list of comments and associated replies to a given content type and object ID.

These actions are explained below.

Setup:
~~~~~~

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
            fields = ('id',
                      ...
                      ...
                      'comments')

        def get_comments(self, obj):
            comments_qs = Comment.objects.filter_by_object(obj)
            return CommentSerializer(comments_qs, many=True).data


By default the image field from profile models will be included inside user object
in JSON response. This can only happen if the profile attributes mentioned early are
defined in your ``settings.py``. In case you would like to serialize more fields from profile models
you need to explicitly declare the ``COMMENT_PROFILE_API_FIELDS`` tuple inside your ``settings.py``
as follows:


.. code:: python

        PROFILE_APP_NAME = 'accounts'
        PROFILE_MODEL_NAME = 'userprofile'
        # the field names below must be similar to your profile model fields
        COMMENT_PROFILE_API_FIELDS = ('display_name', 'birth_date', 'image')


Comment API actions:
~~~~~~~~~~~~~~~~~~~~

    **1- Retrieve the list of comments and associated replies to a given content type and object ID:**

    This action can be performed by providing the url with data queries related to the content type.

    Get request accepts 3 params:


    - ``type``: is the model name of the content type that have comments associated with it.
    - ``id``: is the id of an object of that model



    For example if you are using axios to retrieve the comment list of second object (id=2) of a model (content type) called post.
    you can do the following:


    .. code:: javascript

        axios ({
            method: "get",
            url: "http://127.0.0.1:8000/api/comments/?type=post&id=2",
        })



    **2- Post a comment and reply to an existing comment:**

    Authorization must be provided in the headers.

    The data queries provided with the url are as above with one more parameter:

    - ``parent_id``: is 0 or **NOT PROVIDED** for parent comments and for reply comments must be the id of parent comment


    Example: posting a parent comment

    .. code:: javascript

        axios({
            method: "post",
            url: "http://127.0.0.1:8000/api/comments/create/?type=post&id=2&parent_id=0",
            data: {
                content: "Hello comments"
            },
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                Authorization: `Token ${token}`
            }
        })


    **3- Update a comment:**

    Authorization must be provided in the headers.

    The url has no data queries in this action.

    This action requires the ``comment id`` that you want to update:


    .. code:: javascript

        axios({
            method: "put",
            url: "http://127.0.0.1:8000/api/comments/1",
            data: {
                content: "Update comment number 1 (id=1)"
            },
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                Authorization: `Token ${token}`
            }
        })


    **4- Delete a comment:**

    Authorization must be provided in the headers.

    The url has no data queries in this action.

    This action requires the ``comment id`` that you want to delete:


    .. code:: javascript

        axios({
            method: "delete",
            url: "http://127.0.0.1:8000/api/comments/1",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                Authorization: `Token ${token}`
            }
        })
