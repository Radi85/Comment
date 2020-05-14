from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from comment.models import Comment, Reaction, ReactionInstance
from test.example.post.models import Post


class BaseCommentTest(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user_1 = user_model.objects.create_user(
                    username="test-1",
                    email="test-1@acme.edu",
                    password="1234"
        )
        self.user_2 = user_model.objects.create_user(
            username="test-2",
            email="test-2@acme.edu",
            password="1234"
        )
        self.client.login(username='test-1', password='1234')
        self.post_1 = Post.objects.create(
            author=self.user_1,
            title="post 1",
            body="first post body"
        )
        self.post_2 = Post.objects.create(
            author=self.user_1,
            title="post 2",
            body="second post body"
        )
        content_type = ContentType.objects.get(model='post')
        self.content_object_1 = content_type.get_object_for_this_type(id=self.post_1.id)
        self.content_object_2 = content_type.get_object_for_this_type(id=self.post_2.id)
        self.increment = 0
        self.reactions = 0

    def create_comment(self, ct_object, parent=None):
        self.increment += 1
        return Comment.objects.create(
            content_object=ct_object,
            content='comment {}'.format(self.increment),
            user=self.user_1,
            parent=parent,
        )

    def create_reaction(self, user, comment, reaction):
        """Increment total reactions, create a new ReactionInstance

        Args:
            user (get_user_model()): user to be associated to the reaction instance
            comment (Comment): comment to be associated with the reaction instance
            reaction (str): reaction to be recorded

        Returns:
            ReactionInstance: The ReactionInstance created
        """
        reaction_type = getattr(ReactionInstance.ReactionType, reaction.upper(), None)
        if reaction_type:
            reaction_obj = Reaction.objects.get(comment=comment)
            return ReactionInstance.objects.create(
                user=user,
                reaction_type=reaction_type.value,
                reaction=reaction_obj
            )
            self.reactions += 1
        raise ValueError('{} is not a valid reaction type'.format(reaction))

    def set_reaction(self, user, comment, reaction):
        """
        Set a reaction using the model function `set_reaction` of ReactionInstance

        Args:
            user (`get_user_model()`): user to be associated with the reaction.
            comment (Comment): comment which needs to set the reaction.
            reaction (str): the reaction to be set.
        """
        ReactionInstance.set_reaction(user, comment, reaction)
