from unittest.mock import patch

from django.core import mail
from django.test import RequestFactory

from comment.conf import settings
from comment.models import Comment, Follower
from comment.api.serializers import get_profile_model, get_user_fields, UserSerializerDAB, CommentCreateSerializer, \
    CommentSerializer
from comment.tests.test_api.test_views import APIBaseTest


class APICommentSerializers(APIBaseTest):
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

    def test_get_profile_model(self):
        # missing settings attrs
        with patch.object(settings, 'PROFILE_APP_NAME', None):
            profile = get_profile_model()
            self.assertIsNone(profile)

        # providing wrong attribute value, an exception is raised
        with patch.object(settings, 'PROFILE_APP_NAME', 'wrong'):
            self.assertRaises(LookupError, get_profile_model)

        # attribute value is None
        with patch.object(settings, 'PROFILE_APP_NAME', None):
            profile = get_profile_model()
            self.assertIsNone(profile)

        # success
        with patch.object(settings, 'PROFILE_APP_NAME', 'user_profile'):
            profile = get_profile_model()
            self.assertIsNotNone(profile)

    def test_user_serializer(self):
        # PROFILE_MODEL_NAME not provided
        with patch.object(settings, 'PROFILE_MODEL_NAME', None):
            profile = UserSerializerDAB.get_profile(self.user_1)
            self.assertIsNone(profile)

        # PROFILE_MODEL_NAME is wrong
        with patch.object(settings, 'PROFILE_MODEL_NAME', 'wrong'):
            profile = UserSerializerDAB.get_profile(self.user_1)
            self.assertIsNone(profile)

        # success
        with patch.object(settings, 'PROFILE_MODEL_NAME', 'userprofile'):
            profile = UserSerializerDAB.get_profile(self.user_1)
            self.assertIsNotNone(profile)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', False)
    def test_create_parent_comment_serializer(self):
        self.assertEqual(self.parent_count, 3)
        self.assertEqual(self.all_count, 8)

        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user_1
        data = {
            'model_obj': self.post_1,
            'parent_comment': None,
            'request': request
        }

        serializer = CommentCreateSerializer(context=data)
        self.assertIsNone(serializer.fields.get('email'))
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
        self.assertEqual(self.parent_count, 3)
        self.assertEqual(self.all_count, 8)

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

    def test_passing_context_to_serializer(self):
        serializer = CommentSerializer(self.comment_1)
        self.assertFalse(serializer.fields['content'].read_only)

        serializer = CommentSerializer(self.comment_1, context={'reaction_update': True})
        self.assertTrue(serializer.fields['content'].read_only)

        serializer = CommentSerializer(self.comment_1, context={'flag_update': True})
        self.assertTrue(serializer.fields['content'].read_only)


class TestProfileSerializer(APIBaseTest):
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
