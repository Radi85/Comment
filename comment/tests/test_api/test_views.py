from time import sleep
from unittest.mock import patch

from django.core import signing, mail
from django.urls import reverse_lazy
from rest_framework import status

from comment.conf import settings
from comment.models import Comment, ReactionInstance
from comment.managers import FlagInstanceManager
from comment.messages import ContentTypeError, EmailError, ReactionError
from comment.api.serializers import CommentSerializer
from comment.utils import get_model_obj
from comment.tests.base import BaseAPITest, timezone
from comment.tests.test_utils import BaseAnonymousCommentTest


class BaseAPIViewTest(BaseAPITest):
    def setUp(self):
        super().setUp()
        self.url_data = {
            'model_name': self.post_1.__class__.__name__.lower(),
            'app_name': self.post_1._meta.app_label,
            'model_id': self.post_1.id,
        }
        self.parents = Comment.objects.filter_parents_by_object(self.post_1).count()
        self.all_comments = Comment.objects.all().count()

    def get_base_url(self):
        raise NotImplementedError

    @staticmethod
    def get_url(base_url, **kwargs):
        if kwargs:
            base_url += '?'
            for (key, val) in kwargs.items():
                base_url += str(key) + '=' + str(val) + '&'
        return base_url.rstrip('&')

    def increase_count(self, parent=False):
        if parent:
            self.parents += 1
        self.all_comments += 1

    def comment_count_test(self):
        self.assertEqual(Comment.objects.filter_parents_by_object(self.post_1).count(), self.parents)
        self.assertEqual(Comment.objects.all().count(), self.all_comments)


class CommentListTest(BaseAPIViewTest):
    @staticmethod
    def get_base_url():
        return reverse_lazy('comment-api:list')

    def test_can_retrieve_all_comments(self):
        response = self.client.get(self.get_url(self.get_base_url(), **self.url_data))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), self.parents)

    def test_retrieving_without_app_name(self):
        data = self.url_data.copy()
        data.pop('app_name')
        url = self.get_url(self.get_base_url(), **data)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.APP_NAME_MISSING)
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_without_model_name(self):
        data = self.url_data.copy()
        data.pop('model_name')
        url = self.get_url(self.get_base_url(), **data)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.MODEL_NAME_MISSING)
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_without_model_id(self):
        url_data = self.url_data.copy()
        url_data.pop('model_id')
        url = self.get_url(self.get_base_url(), **url_data)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.MODEL_ID_MISSING)
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_with_invalid_app_name(self):
        data = self.url_data.copy()
        app_name = 'invalid'
        data['app_name'] = app_name
        url = self.get_url(self.get_base_url(), **data)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.APP_NAME_INVALID.format(app_name=app_name))
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_with_invalid_model_name(self):
        url_data = self.url_data.copy()
        model_name = 'does_not_exists'
        url_data['model_name'] = model_name
        url = self.get_url(self.get_base_url(), **url_data)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.MODEL_NAME_INVALID.format(model_name=model_name))
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_with_non_exitsting_model_id(self):
        url_data = self.url_data.copy()
        model_id = 100
        url_data['model_id'] = model_id
        url = self.get_url(self.get_base_url(), **url_data)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['detail'],
            ContentTypeError.MODEL_ID_INVALID.format(model_id=model_id, model_name=url_data["model_name"])
        )
        self.assertTextTranslated(response.data['detail'], url)

    def test_retrieving_with_non_int_model_id(self):
        url_data = self.url_data.copy()
        model_id = 'c'
        url_data['model_id'] = model_id
        url = self.get_url(self.get_base_url(), **url_data)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['detail'],
            ContentTypeError.ID_NOT_INTEGER.format(var_name='model', id=model_id)
        )
        self.assertTextTranslated(response.data['detail'], url)


class CommentCreateTest(BaseAPIViewTest):
    def get_base_url(self):
        return reverse_lazy('comment-api:create')

    def test_create_parent_comment(self):
        data = {'content': 'new parent comment from api'}
        url_data = self.url_data.copy()

        response = self.client.post(self.get_url(self.get_base_url(), **url_data), data=data)

        self.assertEqual(response.status_code, 201)
        comment_id = response.json()['id']
        # test email in database for authenticated user
        self.assertEqual(Comment.objects.get(id=comment_id).email, response.wsgi_request.user.email)
        self.increase_count(parent=True)
        self.comment_count_test()

    def test_create_child_comment(self):
        url_data = self.url_data.copy()
        model_obj = get_model_obj(**url_data)
        url_data['parent_id'] = Comment.objects.all_comments_by_object(model_obj).filter(parent=None).first().id
        data = {'content': 'new child comment from api'}

        response = self.client.post(self.get_url(self.get_base_url(), **url_data), data=data)

        self.assertEqual(response.status_code, 201)
        self.increase_count()
        self.comment_count_test()

    def create_parent_comment_with_parent_id_0(self):
        url_data = self.url_data.copy()
        url_data['parent_id'] = 0
        data = {'content': 'new comment from api'}

        response = self.client.post(self.get_url(self.get_base_url(), **url_data), data=data)

        self.assertEqual(response.status_code, 201)
        self.increase_count(parent=True)
        self.comment_count_test()

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_for_anonymous_with_invalid_data(self):
        base_url = self.get_base_url()
        url_data = self.url_data.copy()
        data = {'content': 'new anonymous comment from api', 'email': ''}
        url = self.get_url(base_url, **url_data)
        self.client.logout()

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['email'], {'email': [EmailError.EMAIL_REQUIRED_FOR_ANONYMOUS]})

    @patch.object(settings, 'COMMENT_ALLOW_ANONYMOUS', True)
    def test_for_anonymous_with_valid_data(self):
        url_data = self.url_data.copy()
        url = self.get_url(self.get_base_url(), **url_data)

        self.client.logout()

        data = {'content': 'new anonymous comment from api', 'email': 'a@a.com'}

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # no count should change
        self.comment_count_test()

    def test_parent_id_not_integer(self):
        base_url = self.get_base_url()
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

    def test_parent_id_does_not_exist(self):
        base_url = self.get_base_url()
        url_data = self.url_data.copy()
        parent_id = 100
        url_data['parent_id'] = parent_id
        data = {'content': 'new child comment from api'}

        response = self.client.post(self.get_url(base_url, **url_data), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.PARENT_ID_INVALID.format(parent_id=parent_id))
        self.assertTextTranslated(response.data['detail'], base_url)

    def test_parent_id_does_not_belong_to_model_object(self):
        base_url = self.get_base_url()
        url_data = self.url_data.copy()
        parent_id = 1
        url_data.update({
            'parent_id': parent_id,
            'model_id': 2
        })
        data = {'content': 'new child comment from api'}

        response = self.client.post(self.get_url(base_url, **url_data), data=data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], ContentTypeError.PARENT_ID_INVALID.format(parent_id=parent_id))
        self.assertTextTranslated(response.data['detail'], base_url)


class CommentDetailTest(BaseAPIViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.c_id = cls.create_comment(cls.content_object_1).id

    def get_base_url(self, c_id=None):
        if not c_id:
            c_id = self.c_id
        return reverse_lazy('comment-api:detail', args=[c_id])

    def test_retrieval(self):
        response = self.client.get(self.get_base_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.c_id)
        self.assertEqual(response.data['content'], Comment.objects.get(id=self.c_id).content)

    def test_update(self):
        data = {'content': 'updated comment'}

        response = self.client.put(self.get_base_url(), data=data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.c_id)
        self.assertEqual(response.data['content'], data['content'])
        self.assertEqual(self.all_comments, Comment.objects.all().count())

    def test_delete_child(self):
        c_id = Comment.objects.exclude(parent=None).first().id
        response = self.client.delete(self.get_base_url(c_id))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(Comment.objects.all().count(), self.all_comments - 1)

    def test_delete_parent(self):
        # delete parent will delete its children as well
        parent = Comment.objects.filter(parent=None).first()
        reply_count = parent.replies().count()

        response = self.client.delete(self.get_base_url(parent.id))

        self.assertEqual(response.status_code, 204)
        # test database change (1 is for the parent comment)
        self.assertEqual(Comment.objects.all().count() + 1 + reply_count, self.all_comments)


class CommentDetailForReactionTest(BaseAPIViewTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = cls.user_1
        cls.comment = cls.create_comment(cls.content_object_1)
        cls.like = ReactionInstance.ReactionType.LIKE.name.lower()
        cls.dislike = ReactionInstance.ReactionType.DISLIKE.name.lower()

    def get_base_url(self, reaction, c_id=None):
        if not c_id:
            c_id = self.comment.id
        return reverse_lazy('comment-api:react', args=[c_id, reaction])

    def test_cannot_update_comment_content(self):
        comment = self.comment
        original_content = comment.content
        data = {'content': 'test updation during reactions'}

        response = self.client.post(self.get_base_url(self.like), data=data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['content'], original_content)

        # test database response
        comment.refresh_from_db()

        self.assertEqual(comment.content, original_content)

    def test_like(self):
        response = self.client.post(self.get_base_url(self.like))

        self.assertEqual(response.status_code, 200)
        self.comment.reaction.refresh_from_db()

        self.assertEqual(self.comment.likes, 1)
        self.assertEqual(self.comment.dislikes, 0)

    def test_dislike_on_liked_comment(self):
        """user has already previously liked the same comment"""
        self.create_reaction_instance(self.user, self.comment, self.like)

        response = self.client.post(self.get_base_url(self.dislike))

        self.assertEqual(response.status_code, 200)
        self.comment.reaction.refresh_from_db()

        self.assertEqual(self.comment.likes, 0)
        self.assertEqual(self.comment.dislikes, 1)

    def test_dislike_on_disliked_comment(self):
        """posting the same reaction twice remvoes the reaction"""
        self.create_reaction_instance(self.user, self.comment, self.dislike)

        response = self.client.post(self.get_base_url(self.dislike))

        self.assertEqual(response.status_code, 200)
        self.comment.reaction.refresh_from_db()

        self.assertEqual(self.comment.likes, 0)
        self.assertEqual(self.comment.dislikes, 0)

    def test_invalid_reaction_type(self):
        reaction = 'invalid_type'
        url = self.get_base_url(reaction)

        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)

        error, = response.data['detail']

        self.assertEqual(error, ReactionError.TYPE_INVALID.format(reaction_type=reaction))
        self.assertTextTranslated(error, url)


class CommentDetailForFlagTest(BaseAPITest):

    def get_base_url(self, c_id=None):
        if not c_id:
            c_id = self.comment.id

        return reverse_lazy('comment-api:flag', args=[c_id])

    def setUp(self):
        super().setUp()
        self.user = self.user_1
        self.flag_data = {
            'reason': FlagInstanceManager.reason_values[0],
            'info': '',
        }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_comment(cls.content_object_1)

    def test_flagging_unflagged_comment(self):
        comment = self.comment
        # this is done as the flag object is deleted in one of the functions and hence sometimes has issues here.
        comment.refresh_from_db()
        data = self.flag_data
        url = self.get_base_url()

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_flagged'])
        comment.flag.refresh_from_db()

        self.assertEqual(comment.flag.count, 1)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_flag_comment_when_flagging_not_enabled(self):
        data = self.flag_data
        url = self.get_base_url()

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 403)

    def test_unflagging_a_flagged_comment(self):
        comment = self.comment_2
        user = self.user_2
        self.create_flag_instance(user, comment)

        self.client.force_login(user)
        url = self.get_base_url(comment.id)

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.count, 0)

    def test_flagging_previous_comments(self):
        """Tries to flag comments created before the flagging migration.
        Maintains backward compatibility"""
        comment = self.comment
        url = self.get_base_url()
        data = self.flag_data
        comment.flag.delete()   # delete the flag object

        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db()
        self.assertEqual(comment.flag.count, 1)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def test_is_flagged_property(self):
        comment = self.create_comment(self.content_object_1)
        data = self.flag_data
        url = self.get_base_url(comment.id)
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

    def test_flagging_with_invalid_reason(self):
        data = self.flag_data.copy()
        data.update({'reason': -1})

        response = self.client.post(self.get_base_url(), data=data)

        self.assertEqual(response.status_code, 400)


class APICommentDetailForFlagStateChangeTest(BaseAPITest):
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

    def get_base_url(self, c_id=None):
        if not c_id:
            c_id = self.comment_1.id
        return reverse_lazy('comment-api:flag-state-change', args=[c_id])

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_when_flagging_is_disabled(self):
        response = self.client.post(self.get_base_url(), data=self.data)

        self.assertEqual(response.status_code, 403)

    def test_when_comment_is_not_flagged(self):
        comment = self.comment_2

        response = self.client.post(self.get_base_url(comment.id), data=self.data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_by_not_permitted_user(self):
        self.client.force_login(self.user_1)

        response = self.client.post(self.get_base_url(), data=self.data)

        self.assertEqual(response.status_code, 403)

    def test_with_wrong_int_value(self):
        data = self.data.copy()

        data['state'] = 100

        response = self.client.post(self.get_base_url(), data=data)

        self.assertEqual(response.status_code, 400)

    def test_with_non_int_value(self):
        data = self.data.copy()
        data['state'] = "Not Int"

        response = self.client.post(self.get_base_url(), data=data)

        self.assertEqual(response.status_code, 400)

    def test_without_data(self):
        response = self.client.post(self.get_base_url(), data={})

        self.assertEqual(response.status_code, 400)

    def test_with_state_as_resolved_on_non_edited_comment(self):
        data = self.data.copy()
        comment = self.comment_1
        data['state'] = comment.flag.RESOLVED

        comment.refresh_from_db()
        self.assertFalse(comment.is_edited)

        response = self.client.post(self.get_base_url(), data=data)

        self.assertEqual(response.status_code, 400)

    def test_success(self):
        comment = self.comment_1
        data = self.data.copy()
        data['state'] = comment.flag.REJECTED

        response = self.client.post(self.get_base_url(), data=data)

        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()

        self.assertEqual(comment.flag.state, comment.flag.REJECTED)

        sleep(1)
        comment.content = "new content"
        comment.save()
        self.assertIs(True, comment.is_edited)

        # First request
        data['state'] = comment.flag.RESOLVED
        response = self.client.post(self.get_base_url(), data=data)
        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.state, comment.flag.RESOLVED)

        # Second request of same state changes state to FLAGGED
        data['state'] = comment.flag.RESOLVED
        response = self.client.post(self.get_base_url(), data=data)
        self.assertEqual(response.status_code, 200)
        comment.flag.refresh_from_db()
        self.assertEqual(comment.flag.state, comment.flag.FLAGGED)


class APIConfirmCommentViewTest(BaseAnonymousCommentTest, BaseAPITest):
    def setUp(self):
        super().setUp()
        self.client.logout()
        self.init_count = Comment.objects.all().count()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment = cls.create_anonymous_comment(posted=timezone.now(), email='a@a.com')

    def get_base_url(self, key=None):
        if not key:
            key = self.key

        return reverse_lazy('comment-api:confirm-comment', args=[key])

    def test_bad_signature(self):
        key = self.key + 'invalid'
        url = self.get_base_url(key)

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
        url = self.get_base_url(key)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['detail'], EmailError.USED_VERIFICATION_LINK)
        self.assertTextTranslated(response.data['detail'], url)
        self.assertEqual(Comment.objects.all().count(), init_count)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_success_without_notification(self):
        response = self.client.get(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comment = Comment.objects.get(email=self.comment_obj.email, posted=self.time_posted)

        self.assertEqual(response.data, CommentSerializer(comment).data)
        self.assertEqual(Comment.objects.all().count(), self.init_count + 1)
        self.assertEqual(len(mail.outbox), 0)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_success_with_notification(self):
        response = self.client.get(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response.renderer_context['view'].email_service._email_thread.join()

        self.assertEqual(len(mail.outbox), 1)


class APIToggleFollowTest(BaseAPITest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_toggle_follow = cls.create_comment(cls.content_object_1)
        cls.app_name = cls.comment_toggle_follow._meta.app_label
        cls.model_name = cls.comment_toggle_follow.__class__.__name__
        cls.model_id = cls.comment_toggle_follow.id

    def get_base_url(self):
        params = [f'app_name={self.app_name}', f'model_name={self.model_name}', f'model_id={self.model_id}']
        base_url = reverse_lazy('comment-api:toggle-subscription')
        return base_url + '?' + '&'.join(params)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_unauthenticated_users(self):
        self.client.logout()

        response = self.client.post(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_system_is_not_enabled(self):
        response = self.client.post(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_toggle_follow(self):
        self.client.force_login(self.user_2)

        self.assertIsNotNone(self.user_2.email)

        response = self.client.post(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json().get('data')
        self.assertEqual(data['app_name'], self.app_name)
        self.assertEqual(data['model_name'], self.model_name)
        self.assertEqual(data['model_id'], self.model_id)
        self.assertTrue(data['following'])


class APIGetSubscribersTest(BaseAPITest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.comment_get_followers = cls.create_comment(cls.content_object_1)
        cls.app_name = cls.comment_get_followers._meta.app_label
        cls.model_name = cls.comment_get_followers.__class__.__name__
        cls.model_id = cls.comment_get_followers.id

    def get_base_url(self):
        params = [f'app_name={self.app_name}', f'model_name={self.model_name}', f'model_id={self.model_id}']
        base_url = reverse_lazy('comment-api:subscribers')
        return base_url + '?' + '&'.join(params)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_unauthenticated_users(self):
        self.client.logout()

        response = self.client.get(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', False)
    def test_system_is_not_enabled(self):
        response = self.client.get(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_only_moderators_can_get_followers(self):
        self.client.force_login(self.moderator)

        response = self.client.get(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['app_name'], self.app_name)
        self.assertEqual(response.data['model_name'], self.model_name)
        self.assertEqual(response.data['model_id'], self.model_id)
        # creator of comment, follow their comment automatically
        self.assertEqual(list(response.data['followers']), [self.comment_get_followers.email])

    @patch.object(settings, 'COMMENT_ALLOW_SUBSCRIPTION', True)
    def test_normal_users_cannot_get_followers(self):
        self.client.force_login(self.user_1)

        response = self.client.get(self.get_base_url())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
