from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from rest_framework import serializers
from comment.models import Comment


def get_model():
    try:
        profile_app_name = settings.PROFILE_APP_NAME
        profile_model_name = settings.PROFILE_MODEL_NAME
    except AttributeError:
        return None
    try:
        content_type = ContentType.objects.get(
            app_label=profile_app_name,
            model=profile_model_name.lower()
        )
    except ContentType.DoesNotExist:
        return None
    except AttributeError:
        return None

    Profile = content_type.model_class()
    return Profile

def get_profile_fields():
    try:
        profile_fields = settings.COMMENT_PROFILE_API_FIELDS
        return profile_fields
    except AttributeError:
        pass

    Profile = get_model()
    if Profile:
        fields = Profile._meta.get_fields()
        for field in fields:
            if hasattr(field, "upload_to"):
                # return tuple of fields to be used directly with the fields attr in Meta class
                return (field.name,)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta():
        model = get_model()
        fields = get_profile_fields()


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
          'id',
          'username',
          'email',
          'profile'
          )

        lookup_field = 'username'

    def get_profile(self, obj):
        try:
            profile = getattr(obj, settings.PROFILE_MODEL_NAME.lower())
        except AttributeError:
            return None
        try:
            return ProfileSerializer(profile).data
        except AttributeError:
            return None


def create_comment_serializer(model_type=None, user=None, pk=None, slug=None, parent_id=None):
    class CommentCreateSerializer(serializers.ModelSerializer):
        user = UserSerializer(read_only=True)
        parent = serializers.SerializerMethodField()
        replies = serializers.SerializerMethodField()
        reply_count = serializers.SerializerMethodField()
        class Meta:
            model = Comment
            fields = (
                'id',
                'user',
                'content',
                'parent',
                'posted_date',
                'edit_date',
                'reply_count',
                'replies',
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
            model_qs = ContentType.objects.filter(model=model_type.lower())
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

        def get_parent(self, obj):
            if obj.parent: # the object has no parent == parent obj
                return obj.parent.id
            else:
                return None

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

    return CommentCreateSerializer


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    parent = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
          'id',
          'user',
          'content',
          'parent',
          'posted_date',
          'edit_date',
          'reply_count',
          'replies',
          )

    def get_parent(self, obj):
        if obj.parent: # the object has no parent == parent obj
            return obj.parent.id
        else:
            return None

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
    parent = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = (
            'id',
            'user',
            'content',
            'parent',
            'posted_date',
            'edit_date'
        )

    def get_parent(self, obj):
        if obj.parent: # the object has no parent == parent obj
            return obj.parent.id
        else:
            return None


class CommentDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    parent = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = (
          'id',
          'user',
          'content',
          'parent',
          'posted_date',
          'edit_date',
          'reply_count',
          'replies',
          )

    def get_parent(self, obj):
        if obj.parent: # the object has no parent == parent obj
            return obj.parent.id
        else:
            return None

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
