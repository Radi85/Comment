import django
from django.conf import settings as django_settings
from django.utils.functional import LazyObject

from comment.conf import defaults as app_settings


_django_version = django.VERSION
DEPRECATED_SETTINGS = {
    'PASSWORD_RESET_TIMEOUT_DAYS' if _django_version > (3, 0) else None,
    'DEFAULT_CONTENT_TYPE' if _django_version > (2, 2) else None,
    'FILE_CHARSET' if _django_version > (2, 2) else None,
    'USE_L10N' if _django_version > (4, 0) else None,
    'USE_TZ' if _django_version > (4, 0) else None,
}


class LazySettings(LazyObject):
    def _setup(self):
        self._wrapped = Settings(app_settings, django_settings)


class Settings(object):
    def __init__(self, *args):
        for item in args:
            for attr in dir(item):
                if attr.isupper() and attr not in DEPRECATED_SETTINGS:
                    setattr(self, attr, getattr(item, attr))


settings = LazySettings()
