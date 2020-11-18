import random
import string
from enum import IntEnum, unique
import hashlib

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import reverse
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.core import signing
from django.apps import apps
from django.contrib.sites.shortcuts import get_current_site

from comment.conf import settings
from comment.messages import ErrorMessage, EmailInfo


@unique
class CommentFailReason(IntEnum):
    BAD = 1
    EXISTS = 2


def get_model_obj(app_name, model_name, model_id):
    content_type = ContentType.objects.get(app_label=app_name, model=model_name.lower())
    model_object = content_type.get_object_for_this_type(id=model_id)
    return model_object


def is_gravatar_enabled():
    return getattr(settings, 'COMMENT_USE_GRAVATAR')


def get_gravatar_img(email):
    if not is_gravatar_enabled() or not email:
        return '/static/img/default.png'
    hashed_email = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f'https://www.gravatar.com/avatar/{hashed_email}'


def get_profile_content_type():
    profile_app_name = getattr(settings, 'PROFILE_APP_NAME', None)
    profile_model_name = getattr(settings, 'PROFILE_MODEL_NAME', None)
    if not profile_app_name or not profile_model_name:
        return None
    try:
        content_type = ContentType.objects.get(
            app_label=profile_app_name,
            model=profile_model_name.lower()
        )
    except ContentType.DoesNotExist:
        return None

    return content_type


def get_profile_instance(user):
    try:
        return getattr(user, settings.PROFILE_MODEL_NAME.lower(), None)
    except AttributeError:
        return None


def has_valid_profile():
    if getattr(settings, 'COMMENT_USE_GRAVATAR'):
        return True

    content_type = get_profile_content_type()
    if not content_type:
        return False
    profile_model = content_type.model_class()
    fields = profile_model._meta.get_fields()
    for field in fields:
        if hasattr(field, "upload_to"):
            return True
    return False


def is_comment_admin(user):
    if settings.COMMENT_FLAGS_ALLOWED:
        return user.groups.filter(name="comment_admin").exists() or (
            user.has_perm("comment.delete_flagged_comment")
            and user.has_perm("comment.delete_comment")
        )
    return False


def is_comment_moderator(user):
    if settings.COMMENT_FLAGS_ALLOWED:
        return user.groups.filter(name="comment_moderator").exists() or user.has_perm(
            "comment.delete_flagged_comment"
        )
    return False


def paginate_comments(comments, comments_per_page, current_page):
    paginator = Paginator(comments, comments_per_page)
    try:
        return paginator.page(current_page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def get_comment_context_data(request, model_object=None):
    app_name = request.GET.get('app_name') or request.POST.get('app_name')
    model_name = request.GET.get('model_name') or request.POST.get('model_name')
    model_id = request.GET.get('model_id') or request.POST.get('model_id')
    if not model_object:
        model_object = get_model_obj(app_name, model_name, model_id)

    comments = model_object.comments.filter_parents_by_object(
        model_object, include_flagged=is_comment_moderator(request.user)
    )
    page = request.GET.get('page') or request.POST.get('page')
    comments_per_page = settings.COMMENT_PER_PAGE
    if comments_per_page:
        comments = paginate_comments(comments, comments_per_page, page)

    login_url = getattr(settings, 'LOGIN_URL')
    if not login_url:
        raise ImproperlyConfigured(ErrorMessage.LOGIN_URL_MISSING)

    if not login_url.startswith('/'):
        login_url = '/' + login_url

    allowed_flags = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    oauth = request.POST.get('oauth') or request.GET.get('oauth')
    if oauth and oauth.lower() == 'true':
        oauth = True
    else:
        oauth = False
    is_anonymous_allowed = settings.COMMENT_ALLOW_ANONYMOUS
    is_translation_allowed = settings.COMMENT_ALLOW_TRANSLATION

    return {
        'model_object': model_object,
        'model_name': model_name,
        'model_id': model_id,
        'app_name': app_name,
        'user': request.user,
        'comments': comments,
        'login_url': login_url,
        'has_valid_profile': has_valid_profile(),
        'allowed_flags': allowed_flags,
        'is_anonymous_allowed': is_anonymous_allowed,
        'is_translation_allowed': is_translation_allowed,
        'oauth': oauth
    }


def id_generator(prefix='', chars=string.ascii_lowercase, len_id=6, suffix=''):
    return prefix + ''.join(random.choice(chars) for _ in range(len_id)) + suffix


def _send_mail(subject, body, sender, receivers,
               fail_silently=False, html=None):
    msg = EmailMultiAlternatives(subject, body, sender, receivers)
    if html:
        msg.attach_alternative(html, 'text/html')
    msg.send(fail_silently)


def send_email_confirmation_request(
    comment, receiver, key, site,
    text_template='comment/anonymous/confirmation_request.txt',
    html_template='comment/anonymous/confirmation_request.html',
    api=False
):
    """Send email requesting comment confirmation"""
    subject = EmailInfo.SUBJECT
    if api:
        confirmation_url = f'/api/comments/confirm/{key}/'
    else:
        confirmation_url = reverse('comment:confirm-comment', args=[key])

    msg_context = {
        'comment': comment,
        'confirmation_url': confirmation_url,
        'contact': settings.COMMENT_CONTACT_EMAIL,
        'site': site
    }
    text_msg_template = loader.get_template(text_template)
    text_msg = text_msg_template.render(msg_context)
    if settings.COMMENT_SEND_HTML_EMAIL:
        html_msg_template = loader.get_template(html_template)
        html_msg = html_msg_template.render(msg_context)
    else:
        html_msg = None

    _send_mail(subject, text_msg, settings.COMMENT_FROM_EMAIL, [receiver], html=html_msg)


def get_comment_from_key(key):
    class TmpComment:
        is_valid = True
        why_invalid = None
        obj = None

    comment = TmpComment()
    comment_model = apps.get_model('comment', 'Comment')
    try:
        comment_dict = signing.loads(str(key))
        model_name = comment_dict.pop('model_name')
        model_id = comment_dict.pop('model_id')
        app_name = comment_dict.pop('app_name')
        comment_dict.update(
            {
                'content_object': get_model_obj(app_name, model_name, model_id),
                'parent': comment_model.objects.get_parent_comment(comment_dict['parent'])
            }
        )
        comment.obj = comment_model(**comment_dict)

    except (ValueError, KeyError, AttributeError, signing.BadSignature):
        comment.is_valid = False
        comment.why_invalid = CommentFailReason.BAD

    if comment.is_valid and comment_model.objects.comment_exists(comment.obj):
        comment.is_valid = False
        comment.why_invalid = CommentFailReason.EXISTS
        comment.obj = None

    if comment.is_valid:
        comment.obj.save()
        comment.obj.refresh_from_db()
    return comment


def process_anonymous_commenting(request, comment, api=False):
    key = signing.dumps(comment.to_dict(), compress=True)
    site = get_current_site(request)
    send_email_confirmation_request(comment, comment.to_dict()['email'], key, site, api=api)
    return EmailInfo.CONFIRMATION_SENT


def get_user_for_request(request):
    if request.user.is_authenticated:
        return request.user
    return None
