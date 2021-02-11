from django.contrib.auth import get_user_model
from django.utils import timezone

from django.apps import apps
from django.db.models import ImageField

from rest_framework import serializers

from comment.conf import settings
from comment.models import Comment, Flag, Reaction
from comment.utils import get_user_for_request, get_profile_instance
from comment.messages import EmailError
from comment.mixins import CommentCreateMixin


def get_profile_model():
    profile_app_name = getattr(settings, 'PROFILE_APP_NAME', None)
    profile_model_name = getattr(settings, 'PROFILE_MODEL_NAME', None)
    if not profile_model_name or not profile_app_name:
        return None
    return apps.get_model(profile_app_name, profile_model_name)


def get_user_fields():
    user_model = get_user_model()
    fields = user_model._meta.get_fields()
    api_fields = list(settings.COMMENT_USER_API_FIELDS) + ['profile']
    api_fields = list(set(api_fields))
    for field in fields:
        if hasattr(field, "upload_to") and isinstance(field, ImageField):
            api_fields.append(field.name)
    return api_fields


class ProfileSerializerDAB(serializers.ModelSerializer):
    class Meta:
        model = get_profile_model()
        fields = getattr(settings, 'COMMENT_PROFILE_API_FIELDS', '__all__')


class UserSerializerDAB(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = get_user_fields()
        lookup_field = model.USERNAME_FIELD

    @staticmethod
    def get_profile(obj):
        profile = get_profile_instance(obj)
        if not profile:
            return None
        return ProfileSerializerDAB(profile).data


class BaseCommentSerializer(serializers.ModelSerializer):
    user = UserSerializerDAB(read_only=True)
    parent = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    @staticmethod
    def get_parent(obj):
        if obj.parent:
            return obj.parent.id
        else:
            return None

    @staticmethod
    def get_replies(obj):
        if obj.is_parent:
            return CommentSerializer(obj.replies(), many=True).data
        else:
            return []

    @staticmethod
    def get_reply_count(obj):
        if obj.is_parent:
            return obj.replies().count()
        else:
            return 0

    @staticmethod
    def get_is_flagged(obj):
        return obj.is_flagged

    @staticmethod
    def get_flags(obj):
        return FlagSerializer(obj.flag).data

    @staticmethod
    def get_reactions(obj):
        return ReactionSerializer(obj.reaction).data


class CommentCreateSerializer(BaseCommentSerializer, CommentCreateMixin):
    class Meta:
        model = Comment
        fields = ('id', 'user', 'email', 'content', 'parent', 'posted', 'edited', 'reply_count', 'replies', 'urlhash')

    def __init__(self, *args, **kwargs):
        user = kwargs['context']['request'].user
        self.email_service = None
        if user.is_authenticated or not settings.COMMENT_ALLOW_ANONYMOUS:
            del self.fields['email']

        super().__init__(*args, **kwargs)

    @staticmethod
    def validate_email(value):
        if not value:
            raise serializers.ValidationError(EmailError.EMAIL_MISSING, code='required')
        return value.strip().lower()

    def create(self, validated_data):
        request = self.context['request']
        user = get_user_for_request(request)
        content = validated_data.get('content')
        email = validated_data.get('email')
        time_posted = timezone.now()

        temp_comment = Comment(
            content_object=self.context['model_obj'],
            content=content,
            user=user,
            parent=self.context['parent_comment'],
            email=email,
            posted=time_posted
        )
        return self.perform_create(temp_comment, request, api=True)


class CommentSerializer(BaseCommentSerializer):
    is_flagged = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'user', 'email', 'content', 'parent', 'posted', 'edited', 'reply_count', 'replies', 'reactions',
            'is_flagged', 'flags', 'urlhash'
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


class ReactionSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()

    class Meta:
        model = Reaction
        fields = ('likes', 'dislikes', 'users')

    @staticmethod
    def get_users(obj):
        users = {'likes': [], 'dislikes': []}
        for instance in obj.reactions.all():
            user_info = {
                'id': instance.user.id,
                'username': instance.user.USERNAME_FIELD
            }

            if instance.reaction_type == instance.ReactionType.LIKE:
                users['likes'].append(user_info)
            else:
                users['dislikes'].append(user_info)
        return users


class FlagSerializer(serializers.ModelSerializer):
    reporters = serializers.SerializerMethodField()
    verbose_state = serializers.SerializerMethodField()

    class Meta:
        model = Flag
        fields = ('count', 'moderator', 'state', 'verbose_state', 'reporters')

    @staticmethod
    def get_reporters(obj):
        return [
            {
                'id': flag_instance.user.id,
                'username': flag_instance.user.USERNAME_FIELD
            }
            for flag_instance in obj.flags.all()
        ]

    @staticmethod
    def get_verbose_state(obj):
        return obj.get_verbose_state(obj.state)
