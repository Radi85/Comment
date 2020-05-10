from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from comment.models import Comment


def get_model_obj(request):
    app_name = request.GET.get('app_name') or request.POST.get('app_name')
    model_name = request.GET.get('model_name') or request.POST.get('model_name')
    model_id = request.GET.get('model_id') or request.POST.get('model_id')
    content_type = ContentType.objects.get(app_label=app_name, model=model_name.lower())
    model_object = content_type.get_object_for_this_type(id=model_id)

    return model_object


def has_valid_profile():
    profile_app_name = getattr(settings, 'PROFILE_APP_NAME', None)
    profile_model_name = getattr(settings, 'PROFILE_MODEL_NAME', None)
    if not profile_app_name or not profile_model_name:
        return False
    try:
        content_type = ContentType.objects.get(
            app_label=profile_app_name,
            model=profile_model_name.lower()
        )
    except ContentType.DoesNotExist:
        return False

    profile_model = content_type.model_class()
    fields = profile_model._meta.get_fields()
    for field in fields:
        if hasattr(field, "upload_to"):
            return True
    return False


def get_comment_context_data(request):
    model_object = get_model_obj(request)
    comments_per_page = request.POST.get('comments_per_page') or request.GET.get('comments_per_page')
    oauth = request.POST.get('oauth') or request.GET.get('oauth')
    page = request.POST.get('currentPage')
    model_name = request.GET.get('model_name')
    model_id = request.GET.get('model_id')
    app_name = request.GET.get('app_name')

    comments = Comment.objects.filter_parents_by_object(model_object)
    if comments_per_page:
        paginator = Paginator(comments, comments_per_page)
        try:
            comments = paginator.page(page)
        except PageNotAnInteger:
            comments = paginator.page(1)
        except EmptyPage:
            comments = paginator.page(paginator.num_pages)

    login_url = getattr(settings, 'LOGIN_URL')

    if not login_url.startswith('/'):
        login_url = '/' + login_url

    context = {
        'model_object': model_object,
        'model_name': model_name,
        'model_id': model_id,
        'app_name': app_name,
        'user': request.user,
        'comments': comments,
        'login_url': login_url,
        'comments_per_page': comments_per_page,
        'has_valid_profile': has_valid_profile(),
        'oauth': oauth
    }

    return context
