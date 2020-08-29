import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(BASE_DIR, 'test/example')

SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key-is-unsafe')
DEBUG = os.environ.get('DEBUG', True) == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split()


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'comment',
    'post.apps.PostConfig',
    'user_profile.apps.AccountsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'test.example.example.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', None),
        'PORT': os.environ.get('DB_PORT', None),
        'CONN_MAX_AGE': 0,
    }
}


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGIN_URL = '/profile/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = LOGIN_URL

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_DIR, 'root/static')
STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'root/media')

PROFILE_APP_NAME = 'user_profile'
PROFILE_MODEL_NAME = 'userprofile'

COMMENT_PROFILE_API_FIELDS = ('display_name', 'birth_date', 'image')
COMMENT_FLAGS_ALLOWED = 2
COMMENT_SHOW_FLAGGED = True

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'user@domain')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'password')
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

COMMENT_ALLOW_ANONYMOUS = True
COMMENT_FROM_EMAIL = os.environ.get('COMMENT_FROM_EMAIL', 'user@doamin')
COMMENT_CONTACT_EMAIL = os.environ.get('COMMENT_CONTACT_EMAIL', 'contact@domain')
COMMENT_SEND_HTML_EMAIL = True
COMMENT_PER_PAGE = 4
