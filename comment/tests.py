from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from comment.models import Comment
from comment.forms import CommentForm
from test.example.post.models import Post


class CreateCommentTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
        	username="radi",
            email="radi@acme.edu",
            password="1234",
    	)
        self.client.login(username='radi', password='1234')
        self.post1 = Post.objects.create(
            author=self.user,
            title="post 1",
            body="first post body"
        )

    def test_create_comment(self):
        # init_all_comments = 0
        init_all_comments = Comment.objects.all().count()
        # init_parent_comments = 0
        init_parent_comments = Comment.objects.all_parent_comments().count()
        # parent comment
        parentcommentform_data = {
            'content': 'parent comment body',
            'app_name': 'post',
            'model':'post',
            'model_id': self.post1.id,
        }
        response_parent = self.client.post(
            reverse('comment:create'),
            parentcommentform_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        parent_comment = Comment.objects.get(
            content='parent comment body',
            object_id=self.post1.id
        )
        self.assertEqual(response_parent.status_code, 200)
        self.assertEqual(parent_comment.parent, None)
        self.assertEqual(
            Comment.objects.all_parent_comments().count(),
            init_parent_comments + 1
            )
        self.assertEqual(Comment.objects.all().count(), init_all_comments + 1)

        # create child comment
        childcommentform_data = {
            'content': 'parent comment body',
            'app_name': 'post',
            'model':'post',
            'model_id': self.post1.id,
            'parent_id': parent_comment.id
        }

        response_child = self.client.post(
            reverse('comment:create'),
            childcommentform_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        child_comment = Comment.objects.get(
            parent= parent_comment
        )
        self.assertEqual(response_child.status_code, 200)
        self.assertEqual(child_comment.parent, parent_comment)
        self.assertEqual(
            Comment.objects.all_parent_comments().count(),
            init_parent_comments + 1)
        self.assertEqual(Comment.objects.all().count(), init_all_comments + 2)


    def test_edit_comment(self):
        content_type = ContentType.objects.get_for_model(self.post1)
        parent_comment = Comment.objects.create(
            content_object=content_type,
            content='parent comment content',
            user=self.user,
        )
        commentform_data = {
            'content': 'parent comment was edited',
        }

        response = self.client.post(
            reverse('comment:edit', kwargs={'pk': parent_comment.id}),
            commentform_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        edited_comment = Comment.objects.get(user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(edited_comment.content, commentform_data['content'])


    def test_delete_comment(self):
        content_type = ContentType.objects.get_for_model(self.post1)
        parent_comment = Comment.objects.create(
            content_object=content_type,
            content='parent comment content',
            user=self.user,
        )
        init_comments = Comment.objects.all().count()
        self.assertEqual(init_comments, 1)
        response = self.client.post(
            reverse('comment:delete', kwargs={'pk': parent_comment.id}),
            # commentform_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.all().count(), init_comments-1)
