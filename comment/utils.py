from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from comment.models import Comment
from comment.forms import CommentForm


def get_model_obj(request):
    if request.method == 'POST':
        content_type = ContentType.objects.get(
            app_label=request.POST.get("app_name"),
            model=request.POST.get("model_name").lower()
        )
        model_object = content_type.get_object_for_this_type(
            id=request.POST.get("model_id")
        )
    else:
        content_type = ContentType.objects.get(
            app_label=request.GET.get("app_name"),
            model=request.GET.get("model_name").lower()
        )
        model_object = content_type.get_object_for_this_type(
            id=request.GET.get("model_id")
        )

    return model_object

def get_view_context(request):
    model_object = get_model_obj(request)
    if request.method == 'POST':

        comments = Comment.objects.filter_by_object(model_object)

        cpp = request.POST.get("cpp", None)
        paginate = request.POST.get("paginate", None)
        if paginate and cpp:
            paginator = Paginator(comments, cpp)
            page = request.POST.get('currentPage')
            try:
                comments = paginator.page(page)
            except PageNotAnInteger:
                comments = paginator.page(1)
            except EmptyPage:
                comments = paginator.page(paginator.num_pages)

        try:
            profile_app_name = settings.PROFILE_APP_NAME
            profile_model_name = settings.PROFILE_MODEL_NAME
        except AttributeError:
            profile_app_name = None
            profile_model_name = None

        try:
            if settings.LOGIN_URL.startswith("/"):
                login_url = settings.LOGIN_URL
            else:
                login_url = "/" + settings.LOGIN_URL
        except AttributeError:
            login_url = ""

        oauth = request.POST.get("oauth")
        context = {
            "commentform": CommentForm(),
            "model_object": model_object,
            "user": request.user,
            "comments": comments,
            "profile_app_name": profile_app_name,
            "profile_model_name": profile_model_name,
            "paginate": paginate,
            "login_url": login_url,
            "cpp": cpp,
            "oauth": oauth

        }
    else:
        cpp = request.GET.get("cpp")
        paginate = request.GET.get("paginate")
        model_name = request.GET.get("model_name")
        model_id = request.GET.get("model_id")
        app_name = request.GET.get("app_name")

        # content_type = ContentType.objects.get(
        #     app_label=app_name,
        #     model=model_name.lower()
        # )
        # model_object = content_type.get_object_for_this_type(
        #     id=model_id
        # )

        oauth = request.GET.get("oauth")
        context = {
            "cpp": cpp,
            "paginate": paginate,
            "model_object": model_object,
            "model_name": model_name,
            "model_id": model_id,
            "app_name": app_name,
            "oauth": oauth
            }

    return context
