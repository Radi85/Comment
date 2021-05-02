from unittest.mock import patch

from django.core import mail
from django.test import RequestFactory

from rest_framework import serializers

from comment.conf import settings
from comment.models import Comment, Follower
from comment.api.serializers import get_profile_model, get_user_fields, UserSerializerDAB, CommentCreateSerializer, \
    CommentSerializer
from comment.tests.test_api.test_views import BaseAPITest
from comment.messages import EmailError


class APICommentSerializersTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.parent_count = Comment.objects.filter_parents_by_object(self.post_1).count()
        self.all_count = Comment.objects.all().count()

    def increase_count(self, parent=False):
        if parent:
            self.parent_count += 1
        self.all_count += 1

    def comment_count_test(self):
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), self.parent_count)
        self.assertEqual(Comment.objects.all().count(), self.all_count)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_create_parent_comment_serializer(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user_1
        data = {
            'model_obj': self.post_1,
            'parent_comment': None,
            'request': request
        }

        serializer = CommentCreateSerializer(context=data)
        self.assertFalse(serializer.fields['email'].required)
        comment = serializer.create(validated_data={'content': 'test'})
        self.increase_count(parent=True)
        self.comment_count_test()
        self.assertIsNotNone(comment)

        # get parent
        parent_id = serializer.get_parent(comment)
        self.assertIsNone(parent_id)

        # get replies
        replies = serializer.get_replies(comment)
        reply_count = serializer.get_reply_count(comment)
        self.assertEqual(replies, [])
        self.assertEqual(reply_count, 0)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_create_child_comment_serializer(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user_1
        data = {
            'model_obj': self.post_1,
            'request': request,
            'parent_comment': self.comment_1
        }

        serializer = CommentCreateSerializer(context=data)
        comment = serializer.create(validated_data={'content': 'test'})
        self.increase_count()
        self.comment_count_test()
        self.assertIsNotNone(comment)

        # get parent
        parent_id = CommentCreateSerializer.get_parent(comment)
        self.assertEqual(parent_id, data['parent_comment'].id)

        replies = serializer.get_replies(self.comment_1)
        reply_count = serializer.get_reply_count(self.comment_1)
        self.assertIsNotNone(replies)
        self.assertEqual(reply_count, 2)

        replies = serializer.get_replies(self.comment_4)
        reply_count = serializer.get_reply_count(self.comment_4)
        self.assertEqual(replies, [])
        self.assertEqual(reply_count, 0)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_send_notification(self):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user_1
        data = {
            'model_obj': self.post_1,
            'request': request,
            'parent_comment': self.comment_1
        }

        Follower.objects.follow('e@e.com', 'testUser', self.comment_1)

        serializer = CommentCreateSerializer(context=data)
        comment = serializer.create(validated_data={'content': 'test'})
        self.assertTrue(serializer.email_service._email_thread.is_alive)
        self.assertIsNotNone(comment)
        self.assertIsNotNone(serializer.email_service._email_thread)
        serializer.email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 1)

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_comment_serializer_for_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        data = {
            'model_obj': self.post_1,
            'parent_comment': None,
            'request': request
        }
        serializer = CommentCreateSerializer(context=data)

        self.assertIsNotNone(serializer.fields['email'])
        comment = serializer.create(validated_data={
            'content': 'anonymous posting',
            'email': 'abc@abc.com'
        })
        # no creation occurs until comment is verified
        self.comment_count_test()
        self.assertIsNotNone(comment)

        # confirmation email is sent
        self.assertIsNotNone(serializer.email_service._email_thread)
        serializer.email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 1)

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_comment_serializer_for_anonymous_missing_email(self):
        from django.contrib.auth.models import AnonymousUser
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        data = {
            'model_obj': self.post_1,
            'parent_comment': None,
            'request': request
        }
        serializer = CommentCreateSerializer(context=data)

        with self.assertRaises(serializers.ValidationError) as e:
            serializer.create(validated_data={'content': 'test'})
        self.assertEqual(e.exception.detail, {'email': [EmailError.EMAIL_REQUIRED_FOR_ANONYMOUS]})

    def test_passing_context_to_serializer(self):
        serializer = CommentSerializer(self.comment_1)
        self.assertFalse(serializer.fields['content'].read_only)

        serializer = CommentSerializer(self.comment_1, context={'reaction_update': True})
        self.assertTrue(serializer.fields['content'].read_only)

        serializer = CommentSerializer(self.comment_1, context={'flag_update': True})
        self.assertTrue(serializer.fields['content'].read_only)


class TestProfileSerializer(BaseAPITest):
    def test_default_fields(self):
        fields = get_user_fields()

        self.assertSetEqual(set(fields), set(settings.COMMENT_USER_API_FIELDS + ['profile']))

    @patch('comment.api.serializers.isinstance')
    @patch('comment.api.serializers.hasattr')
    def test_has_image_field(self, mocked_hasattr, mocked_isinstance):
        mocked_isinstance.return_value = True
        mocked_hasattr.return_value = True
        fields = get_user_fields()

        self.assertIs('logentry' in fields, True)


class GetProfileTest(BaseAPITest):
    @patch.object(settings, 'PROFILE_APP_NAME', None)
    def test_setting_attribute_not_set(self):
        profile = get_profile_model()

        self.assertIsNone(profile)

    @patch.object(settings, 'PROFILE_APP_NAME', 'wrong')
    def test_setting_attribute_set_wrong(self):
        self.assertRaises(LookupError, get_profile_model)

    @patch.object(settings, 'PROFILE_APP_NAME', 'user_profile')
    def tests_success(self):
        profile = get_profile_model()

        self.assertIsNotNone(profile)


class TestUserSerializer(BaseAPITest):
    @patch.object(settings, 'PROFILE_MODEL_NAME', None)
    def test_profile_model_name_not_provided(self):
        profile = UserSerializerDAB.get_profile(self.user_1)

        self.assertIsNone(profile)

    @patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong')
    def test_profile_model_wrong(self):
        profile = UserSerializerDAB.get_profile(self.user_1)

        self.assertIsNone(profile)

    @patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile')
    def test_success(self):
        profile = UserSerializerDAB.get_profile(self.user_1)

        self.assertIsNotNone(profile)
