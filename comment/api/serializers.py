from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers
from comment.models import Comment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
          'id',
          'username',)

        lookup_field = 'username'


def create_comment_serializer(model_type=None, user=None, pk=None, slug=None, parent_id=None):
    class CommentCreateSerializer(serializers.ModelSerializer):
        user = UserSerializer(read_only=True)
        class Meta:
            model = Comment
            fields = (
                'id',
                'user',
                'content',
                'posted_date',
                'edit_date',
            )
        def __init__(self, *args, **kwargs):
            self.model_type = model_type
            self.pk = pk
            self.slug = slug
            self.parent_obj = None
            if parent_id:
                parent_qs = Comment.objects.filter(id=parent_id)
                if parent_qs.exists() and parent_qs.count() == 1:
                    self.parent_obj = parent_qs.first()
            return super(CommentCreateSerializer, self).__init__(*args, **kwargs)

        def validate(self, data):
            model_type = self.model_type
            model_qs = ContentType.objects.filter(model=model_type)
            if not model_qs.exists() and model_qs.count() != 1:
                raise serializers.ValidationError(
                    "this is not a valid content type"
                    )
            Model = model_qs.first().model_class()
            model_obj = Model.objects.filter(Q(id=self.pk)|Q(slug=self.slug))
            if not model_obj.exists() and model_obj.count() != 1:
                raise serializers.ValidationError(
                    "this is not a valid id or slug for this model"
                    )
            return data

        def create(self, validated_data):
            content = validated_data.get("content")
            model_type = self.model_type
            slug = self.slug
            pk = self.pk
            parent_obj = self.parent_obj
            comment = Comment.objects.create_by_model_type(
                    model_type, pk, slug, content, user,
                    parent_obj=parent_obj,
                    )
            return comment

    return CommentCreateSerializer

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
          'id',
          'user',
          'content',
          'posted_date',
          'edit_date',
          'reply_count',
          'replies',
          )

    def get_replies(self, obj):
        if not obj.parent: # the object has no parent == parent obj
            return CommentChildSerializer(obj.replies, many=True).data
        else:
            return None

    def get_reply_count(self, obj):
        if not obj.parent: # the object has no parent == parent obj
            return obj.replies.count()
        else:
            return None


class CommentChildSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = (
            'id',
            'user',
            'content',
            'posted_date',
            'edit_date'
        )


class CommentDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    parent = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = (
          'id',
          'user',
          'content',
          'parent',
          'posted_date',
          'edit_date',
          )

    def get_parent(self, obj):
        if obj.parent: # the object has no parent == parent obj
            return obj.parent.id
        else:
            return None
