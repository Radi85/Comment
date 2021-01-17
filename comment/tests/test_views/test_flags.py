from unittest.mock import patch

from rest_framework import status

from comment.conf import settings
from comment.messages import FlagInfo, FlagError
from comment.tests.base import BaseCommentFlagTest


class SetFlagViewTest(BaseCommentFlagTest):
    def setUp(self):
        super().setUp()
        self.flag_data.update({
            'info': ''
            })
        self.response_data = {
            'status': 1
        }

    def test_set_flag(self):
        _url = self.get_url('comment:flag', self.comment.id)
        self.flag_data['reason'] = 1
        response = self.client.post(_url, data=self.flag_data)

        response_data = {
            'data': {
                'status': 0,
                'flag': 1,
            },
            'anonymous': False,
            'error': None,
            'msg': FlagInfo.FLAGGED_SUCCESS
        }
        self.assertEqual(response.status_code, 200)
        server_response = response.json()
        self.assertDictEqual(server_response, response_data)
        self.assertTextTranslated(server_response['msg'], _url)

    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    def test_set_flag_when_flagging_not_enabled(self):
        settings.COMMENT_FLAGS_ALLOWED = 0
        _url = self.get_url('comment:flag', self.comment.id)
        self.flag_data['reason'] = 1
        response = self.client.post(_url, data=self.flag_data)
        self.assertEqual(response.status_code, 403)

    def test_set_flag_for_flagging_old_comments(self):
        """Test backward compatibility for this update"""
        _url = self.get_url('comment:flag', self.comment.id)
        data = self.flag_data.copy()
        # delete the flag object
        self.comment.flag.delete()
        response = self.client.post(_url, data=data)
        response_data = {
            'data': {
                'status': 0,
                'flag': 1,
            },
            'anonymous': False,
            'error': None,
            'msg': FlagInfo.FLAGGED_SUCCESS
        }
        self.assertEqual(response.status_code, 200)
        server_response = response.json()
        self.assertDictEqual(server_response, response_data)
        self.assertTextTranslated(server_response['msg'], _url)

    def test_set_flag_for_unflagging(self):
        # un-flag => no reason is passed and the comment must be already flagged by the user
        _url = self.get_url('comment:flag', self.comment_2.id)
        data = {}
        response = self.client.post(_url, data=data)
        response_data = {
            'data': {
                'status': 0
            },
            'anonymous': False,
            'error': None,
            'msg': FlagInfo.UNFLAGGED_SUCCESS
        }
        self.assertEqual(response.status_code, 200)
        server_response = response.json()
        self.assertDictEqual(server_response, response_data)
        self.assertTextTranslated(server_response['msg'], _url)

    def test_set_flag_for_unauthenticated_user(self):
        """Test whether unauthenticated user can create/delete flag using view"""
        url = self.get_url('comment:flag', self.comment.id).replace('?', '')
        self.client.logout()
        response = self.client.post(url, data=self.flag_data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '{}?next={}'.format(settings.LOGIN_URL, url))

    def test_get_request(self):
        """Test whether GET requests are allowed or not"""
        url = self.get_url('comment:flag', self.comment.id)
        response = self.client.get(url, data=self.flag_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_non_ajax_requests(self):
        """Test response if non AJAX requests are sent"""
        url = self.get_url('comment:flag', self.comment.id)
        response = self.client_non_ajax.post(url, data=self.flag_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_incorrect_comment_id(self):
        """Test response when an incorrect comment id is passed"""
        url = self.get_url('comment:flag', 102_876)
        response = self.client.post(url, data=self.flag_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_incorrect_reason(self):
        """Test response when incorrect reason is passed"""
        url = self.get_url('comment:flag', self.comment.id)
        data = self.flag_data
        reason = -1
        data.update({'reason': reason})
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)


class ChangeFlagStateViewTest(BaseCommentFlagTest):
    @patch.object(settings, 'COMMENT_FLAGS_ALLOWED', 1)
    def setUp(self):
        super().setUp()
        self.data = {
            'state': self.comment_for_change_state.flag.REJECTED
        }
        self.create_flag_instance(self.user_1, self.comment_for_change_state, **self.flag_data)
        self.create_flag_instance(self.user_2, self.comment_for_change_state, **self.flag_data)

    def test_change_flag_state_for_unflagged_comment(self):
        comment = self.create_comment(self.content_object_1)
        self.assertFalse(comment.is_flagged)
        self.client.force_login(self.moderator)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.moderator.id)
        response = self.client.post(self.get_url('comment:flag-change-state', comment.id), data=self.data)
        self.assertEqual(response.status_code, 400)

    def test_change_flag_state_by_not_permitted_user(self):
        self.assertTrue(self.comment_for_change_state.is_flagged)
        self.client.force_login(self.user_1)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user_1.id)
        response = self.client.post(
            self.get_url('comment:flag-change-state', self.comment_for_change_state.id), data=self.data
        )
        self.assertEqual(response.status_code, 403)

    def test_change_flag_state_with_wrong_state_value(self):
        self.assertTrue(self.comment_for_change_state.is_flagged)
        self.client.force_login(self.moderator)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.moderator.id)
        self.assertEqual(self.comment_for_change_state.flag.state, self.comment_for_change_state.flag.FLAGGED)

        # valid state is REJECTED and RESOLVED
        self.data['state'] = self.comment_for_change_state.flag.UNFLAGGED
        response = self.client.post(
            self.get_url('comment:flag-change-state', self.comment_for_change_state.id), data=self.data
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], FlagError.STATE_CHANGE_ERROR)
        self.assertEqual(self.comment_for_change_state.flag.state, self.comment_for_change_state.flag.FLAGGED)

    def test_change_flag_state_success(self):
        self.assertTrue(self.comment_for_change_state.is_flagged)
        self.client.force_login(self.moderator)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.moderator.id)
        self.assertEqual(self.comment_for_change_state.flag.state, self.comment_for_change_state.flag.FLAGGED)

        # valid state is REJECTED and RESOLVED
        self.data['state'] = self.comment_for_change_state.flag.REJECTED
        response = self.client.post(
            self.get_url('comment:flag-change-state', self.comment_for_change_state.id), data=self.data
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['state'], self.comment_for_change_state.flag.REJECTED)
        self.comment_for_change_state.flag.refresh_from_db()
        self.assertEqual(self.comment_for_change_state.flag.moderator, self.moderator)
        self.assertEqual(self.comment_for_change_state.flag.state, self.comment_for_change_state.flag.REJECTED)
