from django.utils.translation import gettext_lazy as _

PROFILE_APP_NAME = None
PROFILE_MODEL_NAME = None
COMMENT_PROFILE_API_FIELDS = []

COMMENT_FLAGS_ALLOWED = 0
COMMENT_SHOW_FLAGGED = False
COMMENT_FLAG_REASONS = [
    (1, _('Spam | Exists only to promote a service')),
    (2, _('Abusive | Intended at promoting hatred')),
]
COMMENT_URL_PREFIX = 'comment-'
COMMENT_URL_SUFFIX = ''
COMMENT_URL_ID_LENGTH = 8
