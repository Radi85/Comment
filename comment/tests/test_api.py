from time import sleep
from unittest.mock import patch

from django.conf import settings
from django.test import RequestFactory

from comment.models import Comment
from comment.api.serializers import get_profile_model, get_user_fields, UserSerializer, CommentCreateSerializer, \
    CommentSerializer
from comment.api.permissions import (
    IsOwnerOrReadOnly, ContentTypePermission, ParentIdPermission, FlagEnabledPermission, CanChangeFlaggedCommentState
)
from comment.api.views import CommentList
from comment.tests.base import BaseCommentTest


class APIBaseTest(BaseCommentTest):
    def setUp(self):
        super().setUp()
        self.comment_1 = self.create_comment(self.content_object_1)
        self.comment_2 = self.create_comment(self.content_object_1)
        self.comment_3 = self.create_comment(self.content_object_1)
        self.comment_4 = self.create_comment(self.content_object_1, parent=self.comment_1)
        self.reaction_1 = self.create_reaction_instance(self.user_1, self.comment_1, 'like')

        self.comment_5 = self.create_comment(self.content_object_2)
        self.comment_6 = self.create_comment(self.content_object_2)
        self.comment_7 = self.create_comment(self.content_object_2, parent=self.comment_5)
        self.comment_8 = self.create_comment(self.content_object_2, parent=self.comment_5)
        self.reaction_2 = self.create_reaction_instance(self.user_1, self.comment_5, 'dislike')

        self.addCleanup(patch.stopall)


class APIPermissionsTest(APIBaseTest):
    def setUp(self):
        super().setUp()
        self.owner_permission = IsOwnerOrReadOnly()
        self.content_type_permission = ContentTypePermission()
        self.parent_permission = ParentIdPermission()
        self.flag_enabled_permission = FlagEnabledPermission()
        self.can_change_flagged_comment_state = CanChangeFlaggedCommentState()
        self.factory = RequestFactory()
        self.view = CommentList()

    def test_owner_permission(self):
        # self.client.login(username='test-2', password='1234')
        request = self.factory.get('/')
        # get is in the safe methods
        self.assertTrue(self.owner_permission.has_object_permission(request, self.view, self.comment_1))

        # PUT method from different user
        request = self.factory.put('/')
        request.user = self.user_2
        self.assertEqual(self.comment_1.user, self.user_1)
        self.assertFalse(self.owner_permission.has_object_permission(request, self.view, self.comment_1))

        # DELETE method from admin
        request = self.factory.put('/')
        request.user = self.admin
        self.assertEqual(self.comment_1.user, self.user_1)
        self.assertFalse(self.owner_permission.has_object_permission(request, self.view, self.comment_1))

        # PUT method from same user
        request = self.factory.put('/')
        request.user = self.user_1
        self.assertEqual(self.comment_1.user, self.user_1)
        self.assertTrue(self.owner_permission.has_object_permission(request, self.view, self.comment_1))

    def test_content_type_permission(self):
        # missing model type
        request = self.factory.get('/api/comments/')
        self.assertFalse(self.content_type_permission.has_permission(request, self.view))
        self.assertEqual(self.content_type_permission.message, 'model type must be provided')

        # missing model id
        request = self.factory.get('/api/comments/?type=post')
        self.assertFalse(self.content_type_permission.has_permission(request, self.view))
        self.assertEqual(self.content_type_permission.message, 'model id must be provided')

        # not exist model type
        request = self.factory.get('/api/comments/?type=not_exist&id=1')
        self.assertFalse(self.content_type_permission.has_permission(request, self.view))
        self.assertEqual(self.content_type_permission.message, 'this is not a valid model type')

        # not exist model id
        request = self.factory.get('/api/comments/?type=post&id=100')
        self.assertFalse(self.content_type_permission.has_permission(request, self.view))
        self.assertEqual(self.content_type_permission.message, 'this is not a valid id for this model')

        # not integer model id
        request = self.factory.get('/api/comments/?type=post&id=c')
        self.assertFalse(self.content_type_permission.has_permission(request, self.view))
        self.assertEqual(self.content_type_permission.message, 'type id must be an integer')

        # success
        self.content_type_permission = ContentTypePermission()  # start fresh
        request = self.factory.get('/api/comments/?type=post&id=1')
        self.assertTrue(self.content_type_permission.has_permission(request, self.view))
        self.assertEqual(self.content_type_permission.message, '')

    def test_parent_id_permission(self):
        # parent id not provided - user will be permitted and parent comment will be created
        request = self.factory.get('/api/comments/create/?type=post&id=1')
        self.assertTrue(self.parent_permission.has_permission(request, self.view))
        self.assertEqual(self.parent_permission.message, '')

        # parent id not int
        request = self.factory.get('/api/comments/create/?type=post&id=1&parent_id=c')
        self.assertFalse(self.parent_permission.has_permission(request, self.view))
        self.assertEqual(self.parent_permission.message, 'the parent id must be an integer')

        # parent id not exist
        request = self.factory.get('/api/comments/create/?type=post&id=1&parent_id=100')
        self.assertFalse(self.parent_permission.has_permission(request, self.view))
        self.assertEqual(
            self.parent_permission.message,
            "this is not a valid id for a parent comment or the parent comment does NOT belong to this model object"
        )

        # parent id doesn't belong to the provided model type
        request = self.factory.get('/api/comments/create/?type=post&id=2&parent_id=1')
        self.assertFalse(self.parent_permission.has_permission(request, self.view))
        self.assertEqual(
            self.parent_permission.message,
            "this is not a valid id for a parent comment or the parent comment does NOT belong to this model object"
        )

        # parent id = 0
        request = self.factory.get('/api/comments/create/?type=post&id=2&parent_id=0')
        self.assertTrue(self.parent_permission.has_permission(request, self.view))

    def test_flag_enabled_permission(self):
        request = self.factory.get('/')
        settings.COMMENT_FLAGS_ALLOWED = 0
        self.assertFalse(self.flag_enabled_permission.has_permission(request, self.view))
        settings.COMMENT_FLAGS_ALLOWED = 1
        self.assertTrue(self.flag_enabled_permission.has_permission(request, self.view))

    def test_can_change_flagged_comment_state(self):
        request = self.factory.get('/')
        request.user = self.user_1  # not moderator user
        self.assertFalse(self.can_change_flagged_comment_state.has_permission(request, self.view))

        request.user = self.moderator
        self.assertTrue(self.can_change_flagged_comment_state.has_permission(request, self.view))

        self.assertFalse(self.comment_1.is_flagged)
        self.assertFalse(
            self.can_change_flagged_comment_state.has_object_permission(request, self.view, self.comment_1)
        )

        flag_data = {
            'reason': '1',
            'info': None,
        }
        settings.COMMENT_FLAGS_ALLOWED = 1
        self.create_flag_instance(self.user_1, self.comment_1, **flag_data)
        self.create_flag_instance(self.user_2, self.comment_1, **flag_data)
        self.assertTrue(self.comment_1.is_flagged)
        self.assertTrue(
            self.can_change_flagged_comment_state.has_object_permission(request, self.view, self.comment_1)
        )

        request.user = self.user_1
        self.assertFalse(
            self.can_change_flagged_comment_state.has_object_permission(request, self.view, self.comment_1)
        )


class APICommentViewsTest(APIBaseTest):
    def test_can_retrieve_comments_list(self):
        response = self.client.get('/api/comments/?type=post&id=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)  # 3 parent comment, child comment will be nested in the parent.

    def test_retrieving_comment_list_fail(self):
        # missing model type
        response = self.client.get('/api/comments/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'model type must be provided')

        # missing model id
        response = self.client.get('/api/comments/?type=post')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'model id must be provided')

        # not exist model type
        response = self.client.get('/api/comments/?type=not_exist&id=1')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'this is not a valid model type')

        # not exist model id
        response = self.client.get('/api/comments/?type=post&id=100')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'this is not a valid id for this model')

        # not integer model id
        response = self.client.get('/api/comments/?type=post&id=c')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'type id must be an integer')

    def test_create_comment(self):
        # create parent comment
        comments_count = Comment.objects.filter_parents_by_object(self.post_1).count()
        all_comments = Comment.objects.all().count()
        self.assertEqual(comments_count, 3)
        self.assertEqual(all_comments, 8)
        data = {'content': 'new parent comment from api'}
        response = self.client.post('/api/comments/create/?type=post&id=1', data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), comments_count + 1)
        self.assertEqual(Comment.objects.all().count(), all_comments + 1)

        # create child comment
        data = {'content': 'new child comment from api'}
        response = self.client.post('/api/comments/create/?type=post&id=1&parent_id=1', data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), comments_count + 1)
        self.assertEqual(Comment.objects.all().count(), all_comments + 2)

        # create comment with parent value = 0
        data = {'content': 'new comment from api'}
        response = self.client.post('/api/comments/create/?type=post&id=1&parent_id=0', data=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), comments_count + 2)
        self.assertEqual(Comment.objects.all().count(), all_comments + 3)

    def test_cannot_create_child_comment(self):
        # parent id not integer
        data = {'content': 'new child comment from api'}
        response = self.client.post('/api/comments/create/?type=post&id=1&parent_id=c', data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['detail'], 'the parent id must be an integer')

        # parent id not exist
        data = {'content': 'new child comment from api'}
        response = self.client.post('/api/comments/create/?type=post&id=1&parent_id=100', data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data['detail'],
            "this is not a valid id for a parent comment or the parent comment does NOT belong to this model object"
        )

        # parent id doesn't belong to the model object
        data = {'content': 'new child comment from api'}
        response = self.client.post('/api/comments/create/?type=post&id=2&parent_id=1', data=data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.data['detail'],
            "this is not a valid id for a parent comment or the parent comment does NOT belong to this model object"
        )

    def test_can_retrieve_update_delete_comment(self):
        count = Comment.objects.all().count()
        self.assertEqual(count, 8)
        # retrieve
        response = self.client.get('/api/comments/2/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], 2)
        self.assertEqual(response.data['content'], 'comment 2')

        # update
        data = {'content': 'updated comment'}
        response = self.client.put('/api/comments/2/', data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], 2)
        self.assertEqual(response.data['content'], data['content'])
        self.assertEqual(count, Comment.objects.all().count())

        # delete
        response = self.client.delete('/api/comments/2/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Comment.objects.all().count(), count - 1)

        # delete parent will delete its children as well
        count = Comment.objects.all().count()
        self.assertEqual(count, 7)
        comment = Comment.objects.get(id=1)
        self.assertEqual(comment.replies().count(), 1)
        response = self.client.delete('/api/comments/1/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Comment.objects.all().count(), count - 2)

    def test_react_to_comment_success(self):
        # post like - comment has no reaction
        self.assertEqual(self.comment_3.likes, 0)
        self.assertEqual(self.comment_3.dislikes, 0)
        response = self.client.post(f'/api/comments/{self.comment_3.id}/react/like/')
        self.assertEqual(response.status_code, 200)
        self.comment_3.reaction.refresh_from_db()
        self.assertEqual(self.comment_3.likes, 1)
        self.assertEqual(self.comment_3.dislikes, 0)

        # post dislike - comment is liked by the user
        response = self.client.post(f'/api/comments/{self.comment_3.id}/react/dislike/')
        self.assertEqual(response.status_code, 200)
        self.comment_3.reaction.refresh_from_db()
        self.assertEqual(self.comment_3.likes, 0)
        self.assertEqual(self.comment_3.dislikes, 1)

        # post dislike - comment is disliked by the user => comment reaction is removed
        response = self.client.post(f'/api/comments/{self.comment_3.id}/react/dislike/')
        self.assertEqual(response.status_code, 200)
        self.comment_3.reaction.refresh_from_db()
        self.assertEqual(self.comment_3.likes, 0)
        self.assertEqual(self.comment_3.dislikes, 0)

    def test_react_to_comment_with_invalid_reaction_type(self):
        response = self.client.post(f'/api/comments/{self.comment_3.id}/react/invalid_type/')
        self.assertEqual(response.status_code, 400)


class APICommentFlagViewTest(APIBaseTest):

    def get_url(self, c_id=None):
        if not c_id:
            c_id = self.comment.id

        return f'/api/comments/{c_id}/flag/'

    def setUp(self):
        super().setUp()
        self.comment = self.comment_1
        self.user = self.user_1
        self.flag = self.create_flag_instance(self.user_2, self.comment_2)
        self.flag_data = {
            'reason': 1,
            'info': '',
        }

    def test_flag_to_comment(self):
        comment = self.comment
        data = self.flag_data
        # flag - comment has no flags
        url = self.get_url()
        self.assertEqual(comment.flag.count, 0)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_flagged'])
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)

    def test_flag_comment_when_flagging_not_enabled(self):
        settings.COMMENT_FLAGS_ALLOWED = 0
        comment = self.comment
        data = self.flag_data
        url = self.get_url()
        self.assertEqual(comment.flag.count, 0)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)
        settings.COMMENT_FLAGS_ALLOWED = 1

    def test_unflag_to_comment(self):
        comment = self.comment_2
        user = self.user_2
        self.client.force_login(user)
        url = self.get_url(comment.id)
        # un-flag - comment is flagged by the user and no reason is passed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.count, 0)

    def test_flag_to_previous_comments(self):
        """Maintains backward compatibility"""
        comment = self.comment
        url = self.get_url()
        data = self.flag_data
        comment.flag.delete()   # delete the flag object
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)

    def test_is_flagged_value(self):
        # test is_flagged property
        comment = self.create_comment(self.content_object_1)
        data = self.flag_data
        url = self.get_url(comment.id)
        settings.COMMENT_FLAGS_ALLOWED = 1
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_flagged'])
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)
        self.client.force_login(self.user_2)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_flagged'])
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.count, 2)

    def test_flag_to_comment_with_invalid_reason(self):
        data = self.flag_data
        data.update({'reason': -1})
        response = self.client.post(self.get_url(), data=data)
        self.assertEqual(response.status_code, 400)


class APICommentDetailForFlagStateChangeTest(APIBaseTest):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.moderator)
        self.data = {
            'state': self.comment_1.flag.REJECTED
        }

    def get_url(self, c_id=None):
        if not c_id:
            c_id = self.comment_1.id
        return f'/api/comments/{c_id}/flag/state/change/'

    def test_change_state_for_unflagged_comment(self):
        self.assertFalse(self.comment_1.is_flagged)
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_state_by_not_permitted_user(self):
        settings.COMMENT_FLAGS_ALLOWED = 1
        flag_data = {
            'reason': '1',
            'info': None,
        }
        self.create_flag_instance(self.user_1, self.comment_1, **flag_data)
        self.create_flag_instance(self.user_2, self.comment_1, **flag_data)
        self.assertTrue(self.comment_1.is_flagged)
        self.client.force_login(self.user_1)
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_state_with_wrong_state_value(self):
        settings.COMMENT_FLAGS_ALLOWED = 1
        flag_data = {
            'reason': '1',
            'info': None,
        }
        self.create_flag_instance(self.user_1, self.comment_1, **flag_data)
        self.create_flag_instance(self.user_2, self.comment_1, **flag_data)
        self.assertTrue(self.comment_1.is_flagged)

        self.data['state'] = 100
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 400)

        self.data['state'] = "Not Int"
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.get_url(), data={})
        self.assertEqual(response.status_code, 400)

        self.data['state'] = self.comment_1.flag.RESOLVED
        self.assertFalse(self.comment_1.is_edited)
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 400)

    def test_change_state_success(self):
        settings.COMMENT_FLAGS_ALLOWED = 1
        flag_data = {
            'reason': '1',
            'info': None,
        }
        self.create_flag_instance(self.user_1, self.comment_1, **flag_data)
        self.create_flag_instance(self.user_2, self.comment_1, **flag_data)
        self.assertTrue(self.comment_1.is_flagged)
        self.assertEqual(self.comment_1.flag.state, self.comment_1.flag.FLAGGED)

        self.data['state'] = self.comment_1.flag.REJECTED
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 200)
        self.comment_1.flag.refresh_from_db()
        self.assertEqual(self.comment_1.flag.state, self.comment_1.flag.REJECTED)

        sleep(1)
        self.comment_1.content = "new content"
        self.comment_1.save()
        self.assertTrue(self.comment_1.is_edited)

        # First request
        self.data['state'] = self.comment_1.flag.RESOLVED
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 200)
        self.comment_1.flag.refresh_from_db()
        self.assertEqual(self.comment_1.flag.state, self.comment_1.flag.RESOLVED)

        # Second request of same state changes state to FLAGGED
        self.data['state'] = self.comment_1.flag.RESOLVED
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 200)
        self.comment_1.flag.refresh_from_db()
        self.assertEqual(self.comment_1.flag.state, self.comment_1.flag.FLAGGED)


class APICommentSerializers(APIBaseTest):
    def test_get_profile_model(self):
        # missing settings attrs
        delattr(settings, 'PROFILE_APP_NAME')
        profile = get_profile_model()
        self.assertIsNone(profile)

        # wrong attribute value
        setattr(settings, 'PROFILE_APP_NAME', 'wrong')
        profile = get_profile_model()
        self.assertIsNone(profile)

        # attribute value is None
        setattr(settings, 'PROFILE_APP_NAME', None)
        profile = get_profile_model()
        self.assertIsNone(profile)

        # success
        setattr(settings, 'PROFILE_APP_NAME', 'user_profile')
        profile = get_profile_model()
        self.assertIsNotNone(profile)

    def test_get_user_fields(self):
        fields = get_user_fields()
        self.assertEqual(fields, ('id', 'username', 'email', 'profile'))

        mocked_hasattr = patch('comment.api.serializers.hasattr').start()
        mocked_hasattr.return_value = True
        fields = get_user_fields()
        self.assertEqual(fields, ('id', 'username', 'email', 'profile', 'logentry'))

    def test_user_serializer(self):
        # PROFILE_MODEL_NAME not provided
        delattr(settings, 'PROFILE_MODEL_NAME')
        profile = UserSerializer.get_profile(self.user_1)
        self.assertIsNone(profile)

        # PROFILE_MODEL_NAME is wrong
        setattr(settings, 'PROFILE_MODEL_NAME', 'wrong')
        profile = UserSerializer.get_profile(self.user_1)
        self.assertIsNone(profile)

        # success
        setattr(settings, 'PROFILE_MODEL_NAME', 'userprofile')
        profile = UserSerializer.get_profile(self.user_1)
        self.assertIsNotNone(profile)

        # user doesn't have profile attribute
        mocked_getattr = patch('comment.api.serializers.getattr').start()
        mocked_getattr.side_effect = [AttributeError]
        profile = UserSerializer.get_profile(self.user_1)
        self.assertIsNone(profile)

    def test_comment_create_serializer(self):
        parent_count = Comment.objects.filter_parents_by_object(self.post_1).count()
        self.assertEqual(parent_count, 3)
        all_count = Comment.objects.all().count()
        self.assertEqual(all_count, 8)
        data = {
            'model_type': 'post',
            'model_id': self.post_1.id,
            'user': self.user_1,
            'parent_id': None,
        }
        serializer = CommentCreateSerializer(context=data)
        comment = serializer.create(validated_data={'content': 'test'})
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), parent_count + 1)
        self.assertEqual(Comment.objects.all().count(), all_count + 1)
        self.assertIsNotNone(comment)

        data['parent_id'] = 0
        serializer = CommentCreateSerializer(context=data)
        comment = serializer.create(validated_data={'content': 'test'})
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), parent_count + 2)
        self.assertEqual(Comment.objects.all().count(), all_count + 2)
        self.assertIsNotNone(comment)

        # get parent
        parent_id = serializer.get_parent(comment)
        self.assertIsNone(parent_id)

        # get replies
        replies = serializer.get_replies(comment)
        reply_count = serializer.get_reply_count(comment)
        self.assertEqual(replies, [])
        self.assertEqual(reply_count, 0)

        data['parent_id'] = 1
        serializer = CommentCreateSerializer(context=data)
        comment = serializer.create(validated_data={'content': 'test'})
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), parent_count + 2)
        self.assertEqual(Comment.objects.all().count(), all_count + 3)
        self.assertIsNotNone(comment)

        # get parent
        parent_id = CommentCreateSerializer.get_parent(comment)
        self.assertEqual(parent_id, 1)

        replies = serializer.get_replies(self.comment_1)
        reply_count = serializer.get_reply_count(self.comment_1)
        self.assertIsNotNone(replies)
        self.assertEqual(reply_count, 2)

        replies = serializer.get_replies(self.comment_4)
        reply_count = serializer.get_reply_count(self.comment_4)
        self.assertEqual(replies, [])
        self.assertEqual(reply_count, 0)

    def test_passing_context_to_serializer(self):
        serializer = CommentSerializer(self.comment_1)
        self.assertFalse(serializer.fields['content'].read_only)

        serializer = CommentSerializer(self.comment_1, context={'reaction_update': True})
        self.assertTrue(serializer.fields['content'].read_only)

        serializer = CommentSerializer(self.comment_1, context={'flag_update': True})
        self.assertTrue(serializer.fields['content'].read_only)
