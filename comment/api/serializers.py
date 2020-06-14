from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from comment.models import Comment


def get_profile_model():
    try:
        content_type = ContentType.objects.get(
            app_label=settings.PROFILE_APP_NAME,
            model=settings.PROFILE_MODEL_NAME.lower()
        )
    except ContentType.DoesNotExist:
        return None
    except AttributeError:
        return None

    profile_class = content_type.model_class()
    return profile_class


def get_user_fields():
    user_model = get_user_model()
    fields = user_model._meta.get_fields()
    for field in fields:
        if hasattr(field, "upload_to"):
            return 'id', 'username', 'email', 'profile', field.name
    return 'id', 'username', 'email', 'profile'


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_profile_model()
        fields = getattr(settings, 'COMMENT_PROFILE_API_FIELDS', '__all__')


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = get_user_fields()
        lookup_field = 'username'

    @staticmethod
    def get_profile(obj):
        if not get_profile_model():
            return None
        try:
            profile = getattr(obj, settings.PROFILE_MODEL_NAME.lower())
        except AttributeError:
            return None

        return ProfileSerializer(profile).data


class BaseCommentSerializer(serializers.ModelSerializer):
    @staticmethod
    def get_parent(obj):
        if obj.parent:
            return obj.parent.id
        else:
            return None

    @staticmethod
    def get_replies(obj):
        if not obj.parent:
            return CommentSerializer(obj.replies(), many=True).data
        else:
            return None

    @staticmethod
    def get_reply_count(obj):
        if not obj.parent:
            return obj.replies().count()
        else:
            return None

    @staticmethod
    def get_likes(obj):
        if hasattr(obj, 'likes'):
            return obj.likes

    @staticmethod
    def get_dislikes(obj):
        if hasattr(obj, 'dislikes'):
            return obj.dislikes

    @staticmethod
    def get_is_flagged(obj):
        return obj.is_flagged


class CommentCreateSerializer(BaseCommentSerializer):
    user = UserSerializer(read_only=True)
    parent = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    is_flagged = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'content', 'parent', 'posted', 'edited', 'reply_count', 'replies', 'likes', 'dislikes',
            'is_flagged'
        )

    def __init__(self, *args, **kwargs):
        self.model_type = kwargs['context'].get('model_type')
        self.model_id = kwargs['context'].get('model_id')
        self.user = kwargs['context'].get('user')
        self.parent_id = kwargs['context'].get('parent_id')
        super().__init__(*args, **kwargs)

    def get_parent_object(self):
        if not self.parent_id or self.parent_id == '0':
            return None
        return Comment.objects.get(id=self.parent_id)

    def create(self, validated_data):
        comment = Comment.objects.create_by_model_type(
            model_type=self.model_type,
            pk=self.model_id,
            user=self.user,
            parent_obj=self.get_parent_object(),
            content=validated_data.get("content")
        )
        return comment


class CommentSerializer(BaseCommentSerializer):
    user = UserSerializer(read_only=True)
    parent = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()
    is_flagged = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'content', 'parent', 'posted', 'edited', 'reply_count', 'replies', 'likes', 'dislikes',
            'is_flagged'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = kwargs.get('context')
        reaction_update = False
        flag_update = False
        if context:
            reaction_update = context.get('reaction_update')
            flag_update = context.get('flag_update')
        if reaction_update or flag_update:
            self.fields['content'].read_only = True
