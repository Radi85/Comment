from django.core.exceptions import ImproperlyConfigured

from comment.conf import settings
from comment.messages import ErrorMessage
from comment.utils import get_request_data, is_comment_moderator, paginate_comments, get_model_obj, has_valid_profile


class DABContext(dict):
    def __init__(self, request, model_object=None, **kwargs):
        self.request = request
        self.app_name = get_request_data(request, 'app_name')
        self.model_name = get_request_data(request, 'model_name')
        self.model_id = get_request_data(request, 'model_id')
        self.model_object = model_object
        if not self.model_object:
            self.model_object = get_model_obj(self.app_name, self.model_name, self.model_id)
        super().__init__(**self(), **kwargs)

    @staticmethod
    def get_login_url():
        login_url = settings.LOGIN_URL
        if not login_url:
            raise ImproperlyConfigured(ErrorMessage.LOGIN_URL_MISSING)
        if not login_url.startswith('/'):
            login_url = '/' + login_url
        return login_url

    def is_oauth(self):
        oauth = get_request_data(self.request, 'oauth')
        if oauth and oauth.lower() == 'true':
            return True
        return False

    def get_comments(self):
        comments = self.model_object.comments.filter_parents_by_object(
            self.model_object, include_flagged=is_comment_moderator(self.request.user)
        )
        page = get_request_data(self.request, 'page')
        comments_per_page = settings.COMMENT_PER_PAGE
        if comments_per_page:
            comments = paginate_comments(comments, comments_per_page, page)
        return comments

    def __call__(self):
        return {
            'model_object': self.model_object,
            'model_name': self.model_name,
            'model_id': self.model_id,
            'app_name': self.app_name,
            'user': self.request.user,
            'comments': self.get_comments(),
            'login_url': self.get_login_url(),
            'has_valid_profile': has_valid_profile(),
            'allowed_flags': settings.COMMENT_FLAGS_ALLOWED,
            'is_anonymous_allowed': settings.COMMENT_ALLOW_ANONYMOUS,
            'is_translation_allowed': settings.COMMENT_ALLOW_TRANSLATION,
            'is_subscription_allowed': settings.COMMENT_ALLOW_SUBSCRIPTION,
            'oauth': self.is_oauth()
        }
