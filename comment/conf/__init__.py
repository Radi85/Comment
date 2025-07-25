import django
from django.conf import settings as django_settings
from django.utils.functional import LazyObject

from comment.conf import defaults as app_settings


_django_version = django.VERSION
DEPRECATED_SETTINGS = {
    'DEFAULT_FILE_STORAGE' if (4, 2) <= _django_version < (5, 1) else None,
    'STATICFILES_STORAGE' if (4, 2) <= _django_version < (5, 1) else None,
    'USE_L10N' if (4, 0) <= _django_version < (5, 0) else None,
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
