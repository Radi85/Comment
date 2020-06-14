from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from comment.models import Comment


def get_model_obj(app_name, model_name, model_id):
    content_type = ContentType.objects.get(app_label=app_name, model=model_name.lower())
    model_object = content_type.get_object_for_this_type(id=model_id)

    return model_object


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


def has_valid_profile():
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
    return user.groups.filter(name='comment_admin').exists() or \
           (user.has_perm('comment.delete_flagged_comment') and user.has_perm('comment.delete_comment'))


def is_comment_moderator(user):
    return user.groups.filter(name='comment_moderator').exists() or user.has_perm('comment.delete_flagged_comment')


def paginate_comments(comments, comments_per_page, current_page):
    paginator = Paginator(comments, comments_per_page)
    try:
        return paginator.page(current_page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def get_comment_context_data(request, model_object=None, comments_per_page=0):
    app_name = request.GET.get('app_name') or request.POST.get('app_name')
    model_name = request.GET.get('model_name') or request.POST.get('model_name')
    model_id = request.GET.get('model_id') or request.POST.get('model_id')
    if not model_object:
        model_object = get_model_obj(app_name, model_name, model_id)

    if not comments_per_page:
        comments_per_page = request.POST.get('comments_per_page') or request.GET.get('comments_per_page')

    comments = Comment.objects.filter_parents_by_object(
        model_object, include_flagged=is_comment_moderator(request.user)
    )

    if comments_per_page:
        page = request.GET.get('page') or request.POST.get('page')
        comments = paginate_comments(comments, comments_per_page, page)

    login_url = getattr(settings, 'LOGIN_URL')
    if not login_url:
        raise ImproperlyConfigured('Comment App: LOGIN_URL is not in the settings')

    if not login_url.startswith('/'):
        login_url = '/' + login_url

    allowed_flags = getattr(settings, 'COMMENT_FLAGS_ALLOWED', 0)
    oauth = request.POST.get('oauth') or request.GET.get('oauth')

    return {
        'model_object': model_object,
        'model_name': model_name,
        'model_id': model_id,
        'app_name': app_name,
        'user': request.user,
        'comments': comments,
        'login_url': login_url,
        'comments_per_page': comments_per_page,
        'has_valid_profile': has_valid_profile(),
        'allowed_flags': allowed_flags,
        'oauth': oauth
    }
