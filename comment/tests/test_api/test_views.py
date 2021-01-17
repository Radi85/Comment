from time import sleep
from unittest.mock import patch

from django.test import RequestFactory
from django.core import signing, mail

from rest_framework import status

from comment.conf import settings
from comment.models import Comment, FlagInstanceManager
from comment.messages import ContentTypeError, EmailError
from comment.api.serializers import CommentSerializer
from comment.api.permissions import (
    IsOwnerOrReadOnly, FlagEnabledPermission, CanChangeFlaggedCommentState, SubscriptionEnabled,
    CanGetSubscribers)
from comment.api.views import CommentList
from comment.tests.base import BaseCommentTest, timezone
from comment.tests.test_utils import BaseAnonymousCommentTest
from comment.utils import is_comment_admin, is_comment_moderator


class APIBaseTest(BaseCommentTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_1 = cls.create_comment(cls.content_object_1)
        cls.comment_2 = cls.create_comment(cls.content_object_1)
        cls.comment_3 = cls.create_comment(cls.content_object_1)
        cls.comment_4 = cls.create_comment(cls.content_object_1, parent=cls.comment_1)
        cls.reaction_1 = cls.create_reaction_instance(cls.user_1, cls.comment_1, 'like')

        cls.comment_5 = cls.create_comment(cls.content_object_2)
        cls.comment_6 = cls.create_comment(cls.content_object_2)
        cls.comment_7 = cls.create_comment(cls.content_object_2, parent=cls.comment_5)
        cls.comment_8 = cls.create_comment(cls.content_object_2, parent=cls.comment_5)
        cls.reaction_2 = cls.create_reaction_instance(cls.user_1, cls.comment_5, 'dislike')

    def setUp(self):
        super().setUp()
        self.addCleanup(patch.stopall)


class APIPermissionsTest(APIBaseTest):
    def setUp(self):
        super().setUp()
        self.owner_permission = IsOwnerOrReadOnly()
        self.flag_enabled_permission = FlagEnabledPermission()
        self.can_change_flagged_comment_state = CanChangeFlaggedCommentState()
        self.subscription_enabled = SubscriptionEnabled()
        self.get_subscribers_permission = CanGetSubscribers()
        self.factory = RequestFactory()
        self.view = CommentList()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag_data = {
            'reason': FlagInstanceManager.reason_values[0],
            'info': '',
        }
        cls.create_flag_instance(cls.user_1, cls.comment_1, **cls.flag_data)
        cls.create_flag_instance(cls.user_2, cls.comment_1, **cls.flag_data)

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

    def test_flag_enabled_permission(self):
        request = self.factory.get('/')
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0):
            self.assertIs(False, self.flag_enabled_permission.has_permission(request, self.view))
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1):
            self.assertIs(True, self.flag_enabled_permission.has_permission(request, self.view))

    def test_can_change_flagged_comment_state(self):
        request = self.factory.get('/')
        user = self.user_1
        request.user = user  # not moderator user
        self.assertFalse(self.can_change_flagged_comment_state.has_permission(request, self.view))

        user = self.moderator
        request.user = user
        self.assertTrue(self.can_change_flagged_comment_state.has_permission(request, self.view))

        comment = self.comment_2
        self.assertFalse(comment.is_flagged)
        self.assertFalse(
            self.can_change_flagged_comment_state.has_object_permission(request, self.view, comment)
        )
        with patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1):
            self.set_flag(self.user_1, comment, **self.flag_data)
            self.set_flag(self.user_2, comment, **self.flag_data)
            self.assertIs(True, comment.is_flagged)
            self.assertIs(
                True,
                self.can_change_flagged_comment_state.has_object_permission(request, self.view, comment)
            )

            request.user = self.user_1
            self.assertIs(
                False,
                self.can_change_flagged_comment_state.has_object_permission(request, self.view, comment)
            )

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_normal_users_cannot_retrieve_subscribers(self):
        request = self.factory.get('/')
        request.user = self.user_1
        self.assertFalse(is_comment_admin(self.user_1))
        self.assertFalse(is_comment_moderator(self.user_1))
        self.assertTrue(settings.COMMENT_ALLOW_SUBSCRIPTION)
        self.assertFalse(self.get_subscribers_permission.has_permission(request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_only_moderators_can_retrieve_subscribers(self):
        request = self.factory.get('/')
        request.user = self.moderator
        self.assertTrue(is_comment_moderator(self.moderator))
        self.assertTrue(settings.COMMENT_ALLOW_SUBSCRIPTION)
        self.assertTrue(self.get_subscribers_permission.has_permission(request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_cannot_retrieve_subscribers_when_system_disabled(self):
        request = self.factory.get('/')
        request.user = self.moderator
        self.assertTrue(is_comment_moderator(self.moderator))
        self.assertFalse(settings.COMMENT_ALLOW_SUBSCRIPTION)
        self.assertFalse(self.get_subscribers_permission.has_permission(request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_cannot_subscribe_when_system_disabled(self):
        request = self.factory.post('/')
        self.assertFalse(settings.COMMENT_ALLOW_SUBSCRIPTION)
        self.assertFalse(self.subscription_enabled.has_permission(request, self.view))

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_can_subscribe(self):
        request = self.factory.post('/')
        self.assertTrue(settings.COMMENT_ALLOW_SUBSCRIPTION)
        self.assertTrue(self.subscription_enabled.has_permission(request, self.view))


class APICommentViewsTest(APIBaseTest):
    def setUp(self):
        super().setUp()
        self.url_data = {
            'model_name': 'post',
            'app_name': 'post',
            'model_id': 1
        }
        self.comment_count = Comment.objects.filter_parents_by_object(self.post_1).count()
        self.all_comments = Comment.objects.all().count()

    @staticmethod
    def get_url(base_url=None, **kwargs):
        if not base_url:
            base_url = '/api/comments/'
        if kwargs:
            base_url += '?'
            for (key, val) in kwargs.items():
                base_url += str(key) + '=' + str(val) + '&'
        return base_url.rstrip('&')

    def increase_count(self, parent=False):
        if parent:
            self.comment_count += 1
        self.all_comments += 1

    def comment_count_test(self):
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), self.comment_count)
        self.assertEqual(Comment.objects.all().count(), self.all_comments)

    def test_can_retrieve_comments_list(self):
        response = self.client.get(self.get_url(**self.url_data))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)  # 3 parent comment, child comment will be nested in the parent.

    def test_retrieving_comment_list_without_app_name(self):
        data = self.url_data.copy()
        data.pop('app_name')
        url = self.get_url(**data)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.APP_NAME_MISSING)
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_comment_list_without_model_name(self):
        data = self.url_data.copy()
        data.pop('model_name')
        url = self.get_url(**data)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.MODEL_NAME_MISSING)
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_comment_list_without_model_id(self):
        url_data = self.url_data.copy()
        url_data.pop('model_id')
        url = self.get_url(**url_data)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.MODEL_ID_MISSING)
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_comment_list_with_invalid_app_name(self):
        data = self.url_data.copy()
        app_name = 'invalid'
        data['app_name'] = app_name
        url = self.get_url(**data)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.APP_NAME_INVALID.format(app_name=app_name))
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_comment_list_with_invalid_model_name(self):
        # not exist model type
        url_data = self.url_data.copy()
        model_name = 'does_not_exists'
        url_data['model_name'] = model_name
        url = self.get_url(**url_data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.MODEL_NAME_INVALID.format(model_name=model_name))
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_comment_list_with_invalid_model_id(self):
        # not exist model id
        url_data = self.url_data.copy()
        model_id = 100
        url_data['model_id'] = model_id
        url = self.get_url(**url_data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['detail'],
            ContentTypeError.MODEL_ID_INVALID.format(model_id=model_id, model_name=url_data["model_name"])
        )
        self.assertTextTranslated(response.data['detail'], url)

        # not integer model id
        model_id = 'c'
        url_data['model_id'] = model_id
        url = self.get_url(**url_data)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['detail'],
            ContentTypeError.ID_NOT_INTEGER.format(var_name='model', id=model_id)
        )
        self.assertTextTranslated(response.data['detail'], url)

    def test_create_parent_comment(self):
        # create parent comment
        self.assertEqual(self.comment_count, 3)
        self.assertEqual(self.all_comments, 8)

        base_url = '/api/comments/create/'
        data = {'content': 'new parent comment from api'}
        url_data = self.url_data.copy()

        response = self.client.post(self.get_url(base_url, **url_data), data=data)
        self.assertEqual(response.status_code, 201)
        comment_id = response.json()['id']
        # test email in database for authenticated user
        self.assertEqual(Comment.objects.get(id=comment_id).email, response.wsgi_request.user.email)
        self.increase_count(parent=True)
        self.comment_count_test()

    def test_create_child_comment(self):
        # create parent comment
        self.assertEqual(self.comment_count, 3)
        self.assertEqual(self.all_comments, 8)

        base_url = '/api/comments/create/'
        url_data = self.url_data.copy()
        # create child comment
        url_data['parent_id'] = 1
        data = {'content': 'new child comment from api'}

        response = self.client.post(self.get_url(base_url, **url_data), data=data)
        self.assertEqual(response.status_code, 201)
        self.increase_count()
        self.comment_count_test()

        # create comment with parent value = 0
        url_data['parent_id'] = 0
        data = {'content': 'new comment from api'}
        response = self.client.post(self.get_url(base_url, **url_data), data=data)
        self.assertEqual(response.status_code, 201)
        self.increase_count(parent=True)
        self.comment_count_test()

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_comment_for_anonymous_with_invalid_data(self):
        base_url = '/api/comments/create/'
        url_data = self.url_data.copy()

        # test anonymous commenting
        self.client.logout()

        # test invalid data
        data = {'content': 'new anonymous comment from api', 'email': ''}
        url = self.get_url(base_url, **url_data)
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['email'], [EmailError.EMAIL_MISSING])
        self.assertTextTranslated(response.json()['email'][0], base_url)

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_create_comment_for_anonymous_with_valid_data(self):
        base_url = '/api/comments/create/'
        url_data = self.url_data.copy()
        url = self.get_url(base_url, **url_data)

        # test anonymous commenting
        self.client.logout()

        # test valid data
        data = {'content': 'new anonymous comment from api', 'email': 'a@a.com'}

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # no count should change
        self.comment_count_test()

    def test_cannot_create_child_comment(self):
        # parent id not integer
        base_url = '/api/comments/create/'
        url_data = self.url_data.copy()
        parent_id = 'c'
        url_data['parent_id'] = parent_id
        data = {'content': 'new child comment from api'}
        response = self.client.post(self.get_url(base_url, **url_data), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['detail'],
            ContentTypeError.ID_NOT_INTEGER.format(var_name='parent', id=parent_id)
        )
        self.assertTextTranslated(response.data['detail'], base_url)

        # parent id not exist
        parent_id = 100
        url_data['parent_id'] = parent_id
        data = {'content': 'new child comment from api'}
        response = self.client.post(self.get_url(base_url, **url_data), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.PARENT_ID_INVALID.format(parent_id=parent_id))
        self.assertTextTranslated(response.data['detail'], base_url)

        # parent id doesn't belong to the model object
        parent_id = 1
        url_data.update({
            'parent_id': parent_id,
            'model_id': 2
        })
        data = {'content': 'new child comment from api'}
        response = self.client.post(self.get_url(base_url, **url_data), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.PARENT_ID_INVALID.format(parent_id=parent_id))

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
        self.flag_data = {
            'reason': FlagInstanceManager.reason_values[0],
            'info': '',
        }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag = cls.create_flag_instance(cls.user_2, cls.comment_2)

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

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_flag_comment_when_flagging_not_enabled(self):
        comment = self.comment
        data = self.flag_data
        url = self.get_url()
        self.assertEqual(comment.flag.count, 0)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

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

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_is_flagged_value(self):
        # test is_flagged property
        comment = self.create_comment(self.content_object_1)
        data = self.flag_data
        url = self.get_url(comment.id)
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIs(False, response.json()['is_flagged'])

        comment.flag.refresh_from_db()

        self.assertEqual(comment.flag.count, 1)
        self.client.force_login(self.user_2)

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIs(True, response.json()['is_flagged'])

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

    @classmethod
    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def setUpTestData(cls):
        super().setUpTestData()
        cls.flag_data = {
            'reason': FlagInstanceManager.reason_values[0],
            'info': None,
        }
        # flag comment_1
        cls.create_flag_instance(cls.user_1, cls.comment_1, **cls.flag_data)
        cls.create_flag_instance(cls.user_2, cls.comment_1, **cls.flag_data)

    def get_url(self, c_id=None):
        if not c_id:
            c_id = self.comment_1.id
        return f'/api/comments/{c_id}/flag/state/change/'

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_change_state_when_flagging_is_disabled(self):
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_state_when_comment_is_not_flagged(self):
        comment = self.comment_2
        self.assertIs(False, comment.is_flagged)
        response = self.client.post(self.get_url(comment.id), data=self.data)
        self.assertEqual(response.status_code, 400)

    def test_change_state_by_not_permitted_user(self):
        comment = self.comment_1
        self.assertIs(True, comment.is_flagged)
        self.client.force_login(self.user_1)
        response = self.client.post(self.get_url(), data=self.data)
        self.assertEqual(response.status_code, 403)

    def test_change_state_with_wrong_state_value(self):
        data = self.data.copy()
        comment = self.comment_1
        self.assertIs(True, comment.is_flagged)

        data['state'] = 100
        response = self.client.post(self.get_url(), data=data)
        self.assertEqual(response.status_code, 400)

        data['state'] = "Not Int"
        response = self.client.post(self.get_url(), data=data)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(self.get_url(), data={})
        self.assertEqual(response.status_code, 400)

        data['state'] = comment.flag.RESOLVED
        comment.refresh_from_db()
        self.assertFalse(comment.is_edited)
        response = self.client.post(self.get_url(), data=data)
        self.assertEqual(response.status_code, 400)

    def test_change_state_success(self):
        comment = self.comment_1
        self.assertIs(True, comment.is_flagged)
        self.assertEqual(comment.flag.state, comment.flag.FLAGGED)

        data = self.data.copy()
        data['state'] = comment.flag.REJECTED
        response = self.client.post(self.get_url(), data=data)
        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.state, comment.flag.REJECTED)

        sleep(1)
        comment.content = "new content"
        comment.save()
        self.assertIs(True, comment.is_edited)

        # First request
        data['state'] = comment.flag.RESOLVED
        response = self.client.post(self.get_url(), data=data)
        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.state, comment.flag.RESOLVED)

        # Second request of same state changes state to FLAGGED
        data['state'] = comment.flag.RESOLVED
        response = self.client.post(self.get_url(), data=data)
        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.state, comment.flag.FLAGGED)


class APIConfirmCommentViewTest(BaseAnonymousCommentTest, APIBaseTest):
    def setUp(self):
        super().setUp()
        self.client.logout()
        self.init_count = Comment.objects.all().count()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_anonymous_comment(posted=timezone.now(), email='a@a.com')

    def get_url(self, key=None):
        if not key:
            key = self.key

        return f'/api/comments/confirm/{key}/'

    def test_bad_signature(self):
        key = self.key + 'invalid'
        url = self.get_url(key)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['detail'], EmailError.BROKEN_VERIFICATION_LINK)
        self.assertTextTranslated(response.data['detail'], url)
        self.assertEqual(Comment.objects.all().count(), self.init_count)

    def test_comment_exists(self):
        comment_dict = self.comment_obj.to_dict().copy()
        init_count = self.init_count
        comment_dict.update({
            'posted': str(self.comment.posted),
            'email': self.comment.email
        })
        key = signing.dumps(comment_dict)
        url = self.get_url(key)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['detail'], EmailError.USED_VERIFICATION_LINK)
        self.assertTextTranslated(response.data['detail'], url)
        self.assertEqual(Comment.objects.all().count(), init_count)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_success_without_notification(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(email=self.comment_obj.email, posted=self.time_posted)
        self.assertEqual(response.data, CommentSerializer(comment).data)
        self.assertEqual(Comment.objects.all().count(), self.init_count + 1)
        self.assertEqual(len(mail.outbox), 0)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_success_with_notification(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response.renderer_context['view'].email_service._email_thread.join()
        self.assertEqual(len(mail.outbox), 1)


class APIToggleFollowTest(APIBaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_toggle_follow = cls.create_comment(cls.content_object_1)
        cls.app_name = cls.comment_toggle_follow._meta.app_label
        cls.model_name = cls.comment_toggle_follow.__class__.__name__
        cls.model_id = cls.comment_toggle_follow.id

    def get_url(self):
        params = [f'app_name={self.app_name}', f'model_name={self.model_name}', f'model_id={self.model_id}']
        return f'/api/comments/toggle-subscription/?{"&".join(params)}'

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_unauthenticated_users(self):
        self.client.logout()
        response = self.client.post(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_system_is_not_enabled(self):
        response = self.client.post(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_toggle_follow(self):
        self.client.force_login(self.user_2)
        self.assertIsNotNone(self.user_2.email)
        response = self.client.post(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json().get('data')
        self.assertEqual(data['app_name'], self.app_name)
        self.assertEqual(data['model_name'], self.model_name)
        self.assertEqual(data['model_id'], self.model_id)
        self.assertTrue(data['following'])


class APIGetSubscribersTest(APIBaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_get_followers = cls.create_comment(cls.content_object_1)
        cls.app_name = cls.comment_get_followers._meta.app_label
        cls.model_name = cls.comment_get_followers.__class__.__name__
        cls.model_id = cls.comment_get_followers.id

    def get_url(self):
        params = [f'app_name={self.app_name}', f'model_name={self.model_name}', f'model_id={self.model_id}']
        return f'/api/comments/subscribers/?{"&".join(params)}'

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_unauthenticated_users(self):
        self.client.logout()
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_system_is_not_enabled(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_only_moderators_can_get_followers(self):
        self.client.force_login(self.moderator)
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['app_name'], self.app_name)
        self.assertEqual(response.data['model_name'], self.model_name)
        self.assertEqual(response.data['model_id'], self.model_id)
        # creator of comment, follow their comment automatically
        self.assertEqual(list(response.data['followers']), [self.comment_get_followers.email])

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_normal_users_cannot_get_followers(self):
        self.client.force_login(self.user_1)
        self.assertFalse(is_comment_moderator(self.user_1))
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
