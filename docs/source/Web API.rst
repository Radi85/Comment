Web API
-------

django-comments-dab uses django-rest-framework to expose a Web API that provides
developers with access to the same functionalities offered through the web user interface.

There are 6 methods available to perform the following actions:


    1. Post a new comment. (Authenticated)

    2. Reply to an existing comment. (Authenticated)

    3. Edit a comment you posted. (Authenticated)

    4. Delete a comment you posted. (Authenticated)

    5. Retrieve the list of all comments and associated replies.

    6. Retrieve the list of comments and associated replies to a given content type and object ID.



Setup:
~~~~~~

To integrate the comment API in your content type (e.g Post model), in serializers.py
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

if you would like to have comment list url in your api root url, include the
comment-list url in the returned response as follows:


.. code:: python

    from rest_framework.decorators import api_view
    from rest_framework.response import Response
    from rest_framework.reverse import reverse

    @api_view(['GET'])
    def api_root(request, format=None):
        return Response({
            'Posts': reverse('post-list', request=request, format=format),
            'comments': reverse('comments-list', request=request, format=format),
        })
