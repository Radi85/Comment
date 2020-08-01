from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from rest_framework import serializers

from comment.conf import settings
from comment.models import Comment, Flag, Reaction
from comment.utils import get_model_obj, process_anonymous_commenting, get_user_for_request


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
    user = UserSerializer(read_only=True)
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


class CommentCreateSerializer(BaseCommentSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'user', 'email', 'content', 'parent', 'posted', 'edited', 'reply_count', 'replies', 'urlhash')

    def __init__(self, *args, **kwargs):
        self.model_name = kwargs['context'].get('model_name')
        self.app_name = kwargs['context'].get('app_name')
        self.model_id = kwargs['context'].get('model_id')
        self.user = kwargs['context'].get('user')
        self.parent_id = kwargs['context'].get('parent_id')
        if kwargs['context']['request'].user.is_authenticated or not settings.COMMENT_ALLOW_ANONYMOUS:
            del self.fields['email']

        super().__init__(*args, **kwargs)

    def validate_email(self, value):
        if (not value):
            raise serializers.ValidationError(
                _('Email is required for posting anonymous comments.'),
                code='required'
                )
        return value.strip().lower()

    def create(self, validated_data):
        request = self.context['request']
        user = get_user_for_request(request)
        content = validated_data.get('content')
        email = validated_data.get('email')
        parent_id = self.parent_id
        time_posted = timezone.now()
        parent_comment = Comment.objects.get_parent_comment(parent_id)
        model_object = get_model_obj(self.app_name, self.model_name, self.model_id)

        comment = Comment(
            content_object=model_object,
            content=content,
            user=user,
            parent=parent_comment,
            email=email,
            posted=time_posted
            )
        dict_comment = {
            'user': user,
            'content': content,
            'email': email,
            'posted': str(time_posted),
            'app_name': self.app_name,
            'model_name': self.model_name,
            'model_id': self.model_id,
            'parent': parent_id
        }
        if settings.COMMENT_ALLOW_ANONYMOUS and (not user):
            process_anonymous_commenting(request, comment, dict_comment, api=True)
        else:
            comment.save()
        return comment


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
            if instance.reaction_type == instance.ReactionType.LIKE:
                users['likes'].append({'id': instance.user.id, 'username': instance.user.username})
            else:
                users['dislikes'].append({'id': instance.user.id, 'username': instance.user.username})
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
            {'id': flag_instance.user.id, 'username': flag_instance.user.username} for flag_instance in obj.flags.all()
        ]

    @staticmethod
    def get_verbose_state(obj):
        return obj.get_verbose_state(obj.state)
