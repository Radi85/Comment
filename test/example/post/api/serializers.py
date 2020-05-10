from rest_framework import serializers

from post.models import Post
from comment.models import Comment
from comment.api.serializers import CommentSerializer


class PostSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        read_only=True,
        lookup_field='username',
    )
    comments = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'url',
            'id',
            'slug',
            'title',
            'body',
            'date',
            'editdate',
            'author',
            'comments'
        )

    @staticmethod
    def get_comments(obj):
        comments_qs = Comment.objects.filter_parents_by_object(obj)
        return CommentSerializer(comments_qs, many=True).data

    @staticmethod
    def get_slug(obj):
        return str(obj.slug)
