from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from comment.models import Comment


def get_profile_model():
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

    Profile = get_profile_model()
    if Profile:
        fields = Profile._meta.get_fields()
        for field in fields:
            if hasattr(field, "upload_to"):
                # return tuple of fields to be used directly with the fields
                # attr in Meta class
                return (field.name,)


def get_user_fields():
    User = get_user_model()
    fields = User._meta.get_fields()
    for field in fields:
        if hasattr(field, "upload_to"):
            return ('id', 'username', 'email', 'profile', field.name)
    return ('id', 'username', 'email', 'profile')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta():
        model = get_profile_model()
        fields = get_profile_fields()


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = get_user_fields()
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


def create_comment_serializer(model_type=None,
                              user=None, pk=None, parent_id=None):
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
            self.parent_obj = None
            return super(CommentCreateSerializer,
                         self).__init__(*args, **kwargs)

        def validate(self, data):
            model_type = self.model_type
            try:
                ct = ContentType.objects.get(model=model_type.lower())
                Model = ct.model_class()
                Model.objects.get(id=self.pk)
            except ContentType.DoesNotExist:
                raise serializers.ValidationError(
                    "this is not a valid content type")
            except Model.DoesNotExist:
                raise serializers.ValidationError(
                    "this is not a valid id for this model"
                    )
            except AttributeError:
                raise serializers.ValidationError(
                    'content type must be specified to create a new comment')
            except ValueError:
                raise serializers.ValidationError(
                    "the id must be an integer"
                    )
            if parent_id:
                parent_obj = None
                try:
                    parent_obj = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    raise serializers.ValidationError(
                        "this is not a valid id for a parent comment"
                        )
                except ValueError:
                    raise serializers.ValidationError(
                        "the parent id must be an integer"
                        )
                self.parent_obj = parent_obj

            return data

        def create(self, validated_data):
            content = validated_data.get("content")
            model_type = self.model_type
            pk = self.pk
            parent_obj = self.parent_obj

            comment = Comment.objects.create_by_model_type(
                    model_type, pk, content, user,
                    parent_obj=parent_obj,
                    )
            return comment

        def get_parent(self, obj):
            # the object has no parent is a parent obj
            if obj.parent:
                return obj.parent.id
            else:
                return None

        def get_replies(self, obj):
            if not obj.parent:
                return CommentSerializer(obj.replies, many=True).data
            else:
                return None

        def get_reply_count(self, obj):
            if not obj.parent:
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

    def get_field_names(self, *args, **kwargs):
        field_names = self.context.get('fields')
        if field_names:
            return field_names
        return super(CommentSerializer, self).get_field_names(*args, **kwargs)

    def get_parent(self, obj):
        if obj.parent:
            return obj.parent.id
        else:
            return None

    def get_replies(self, obj):
        if not obj.parent:
            child_fields = ['id', 'user', 'content', 'parent',
                            'posted_date', 'edit_date']
            return CommentSerializer(
                obj.replies,
                many=True,
                context={'fields': child_fields}).data
        else:
            return None

    def get_reply_count(self, obj):
        if not obj.parent:
            return obj.replies.count()
        else:
            return None
