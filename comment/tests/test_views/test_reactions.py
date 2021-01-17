from django.urls import reverse
from rest_framework import status

from comment.tests.base import BaseCommentViewTest
from comment.messages import ReactionInfo
from comment.conf import settings


class SetReactionViewTest(BaseCommentViewTest):
    def setUp(self):
        super().setUp()
        self.comment = self.create_comment(self.content_object_1)

    @staticmethod
    def get_reaction_url(obj_id, action):
        return reverse('comment:react', kwargs={
            'pk': obj_id,
            'reaction': action
        })

    def test_set_reaction_for_authenticated_users(self):
        """Test whether users can create/change reactions using view"""
        _url = self.get_reaction_url(self.comment.id, 'like')
        response = self.client.post(_url)
        data = {
            'data': {
                'status': 0,
                'likes': 1,
                'dislikes': 0,
            },
            'msg': ReactionInfo.UPDATED_SUCCESS,
            'anonymous': False,
            'error': None,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        server_response = response.json()
        self.assertDictEqual(server_response, data)
        self.assertTextTranslated(server_response['msg'], _url)

    def test_set_reaction_for_old_comments(self):
        """Test backward compatibility for this update"""
        _url = self.get_reaction_url(self.comment.id, 'like')
        # delete the reaction object
        self.comment.reaction.delete()
        response = self.client.post(_url)
        data = {
            'data': {
                'status': 0,
                'likes': 1,
                'dislikes': 0,
            },
            'msg': ReactionInfo.UPDATED_SUCCESS,
            'anonymous': False,
            'error': None,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        server_response = response.json()
        self.assertDictEqual(server_response, data)
        self.assertTextTranslated(server_response['msg'], _url)

    def test_set_reaction_for_unauthenticated_users(self):
        """Test whether unauthenticated users can create/change reactions using view"""
        _url = self.get_reaction_url(self.comment.id, 'dislike')
        self.client.logout()
        response = self.client.post(_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '{}?next={}'.format(settings.LOGIN_URL, _url))

    def test_get_request(self):
        """Test whether GET requests are allowed or not"""
        _url = self.get_reaction_url(self.comment.id, 'like')
        response = self.client.get(_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_non_ajax_requests(self):
        """Test response if non AJAX requests are sent"""
        _url = self.get_reaction_url(self.comment.id, 'like')
        response = self.client_non_ajax.post(_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_incorrect_comment_id(self):
        """Test response when an incorrect comment id is passed"""
        _url = self.get_reaction_url(102_876, 'like')
        response = self.client.post(_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_incorrect_reaction(self):
        """Test response when incorrect reaction is passed"""
        _url = self.get_reaction_url(self.comment.id, 'likes')
        response = self.client.post(_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test incorrect type
        _url = self.get_reaction_url(self.comment.id, 1)
        response = self.client.post(_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
