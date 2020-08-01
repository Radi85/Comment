from django.utils.translation import gettext_lazy as _
from django.conf import settings

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
COMMENT_PER_PAGE = 10
COMMENT_ALLOW_ANONYMOUS = False
if getattr(settings, 'COMMENT_ALLOW_ANONYMOUS', COMMENT_ALLOW_ANONYMOUS):
    COMMENT_FROM_EMAIL = settings.EMAIL_HOST_USER   # used for sending confirmation emails
    COMMENT_CONTACT_EMAIL = COMMENT_FROM_EMAIL  # used for contact address in confirmation emails
    COMMENT_SEND_HTML_EMAIL = True
    COMMENT_ANONYMOUS_USERNAME = 'Anonymous User'
