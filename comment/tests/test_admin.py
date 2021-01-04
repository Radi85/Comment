from django.apps import apps
from django.contrib import admin

from comment.tests.base import BaseCommentTest
from comment.models import FlagInstance, ReactionInstance


class TestCommentAdmin(BaseCommentTest):
    def test_all_models_are_registered(self):
        app = apps.get_app_config('comment')
        models = app.get_models()

        for model in models:
            try:
                self.assertIs(
                    True,
                    admin.site.is_registered(model),
                    msg=f'Did you forget to register the "{model.__name__}" in the django-admin?')
            except AssertionError as exception:
                # these models have been registred as inlines in the admin.
                if model in [ReactionInstance, FlagInstance]:
                    continue
                else:
                    raise exception
