from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType

from comment.models import Comment, ReactionInstance
from comment.forms import CommentForm
from comment.utils import has_valid_profile

register = template.Library()


@register.simple_tag(name='get_model_name')
def get_model_name(obj):
    """ returns the model name of an object """
    return type(obj).__name__


@register.simple_tag(name='get_app_name')
def get_app_name(obj):
    """ returns the app name of an object """
    return type(obj)._meta.app_label


@register.simple_tag(name='get_comment_count')
def get_comment_count(obj):
    """ returns the count of comment of an object """
    model_object = type(obj).objects.get(id=obj.id)
    return model_object.comments.all().count()


@register.simple_tag(name='get_profile_url')
def get_profile_url(obj):
    """ returns profile url of user """
    profile_app_name = getattr(settings, 'PROFILE_APP_NAME', None)
    profile_model_name = getattr(settings, 'PROFILE_MODEL_NAME', None)
    if not profile_app_name or not profile_model_name:
        return ''
    try:
        content_type = ContentType.objects.get(
            app_label=profile_app_name,
            model=profile_model_name.lower()
        )
        profile = content_type.get_object_for_this_type(user=obj.user)
        return profile.get_absolute_url()
    except ContentType.DoesNotExist:
        return ''


@register.simple_tag(name='get_img_path')
def get_img_path(obj):
    """ returns url of profile image of a user """
    profile_app_name = getattr(settings, 'PROFILE_APP_NAME', None)
    profile_model_name = getattr(settings, 'PROFILE_MODEL_NAME', None)
    if not profile_app_name or not profile_model_name:
        return ''
    try:
        content_type = ContentType.objects.get(
            app_label=profile_app_name,
            model=profile_model_name.lower()
        )
    except ContentType.DoesNotExist:
        return ''

    profile_model = content_type.model_class()
    fields = profile_model._meta.get_fields()
    profile = content_type.model_class().objects.get(user=obj.user)
    for field in fields:
        if hasattr(field, 'upload_to'):
            return field.value_from_object(profile).url
    return ''


def render_comments(obj, request, oauth=False, comments_per_page=10):
    """
    Retrieves list of comment related to a certain object and renders the appropriate template
    """
    model_object = type(obj).objects.get(id=obj.id)
    comments = Comment.objects.filter_parents_by_object(model_object)

    if comments_per_page:
        paginator = Paginator(comments, comments_per_page)
        page = request.GET.get('page')
        try:
            comments = paginator.page(page)
        except PageNotAnInteger:
            comments = paginator.page(1)
        except EmptyPage:
            comments = paginator.page(paginator.num_pages)

    login_url = getattr(settings, 'LOGIN_URL', None)
    if not login_url:
        raise ImproperlyConfigured('Comment App: LOGIN_URL is not in the settings')

    if not login_url.startswith('/'):
        login_url = '/' + login_url

    context = {
        'comment_form': CommentForm(),
        'model_object': obj,
        'user': request.user,
        'comments': comments,
        'oauth': oauth,
        'login_url': login_url,
        'has_valid_profile': has_valid_profile(),
        'comments_per_page': comments_per_page
    }
    return context


register.inclusion_tag('comment/base.html')(render_comments)


def include_static():
    """ include static files """
    return None


register.inclusion_tag('comment/static.html')(include_static)


def include_static_jquery():
    """ include static files """
    return None


register.inclusion_tag('comment/static_jquery.html')(include_static_jquery)


def include_bootstrap():
    """ include static files """
    return None


register.inclusion_tag('comment/bootstrap.html')(include_bootstrap)


@register.simple_tag(name='render_field')
def render_field(field, **kwargs):
    field.field.widget.attrs.update(kwargs)
    return field


@register.simple_tag(name='has_reacted')
def has_reacted(comment, user, reaction):
    """
    Returns whether a user has reacted with a particular reaction on a comment or not.

    Args:
        comment_and_user : tuple
            arg1(comment:comment): comment to be queried about.
            arg2(user:User): user to be queried about.
        reaction (str): reaction to be queried about.

    Returns:
        bool
    """
    if user.is_authenticated:
        reaction_type = getattr(ReactionInstance.ReactionType, reaction.upper(), None)
        if not reaction_type:
            raise template.TemplateSyntaxError(
                'Reaction must be an valid ReactionManager.RelationType. {} is not'.format(reaction)
                )
        return ReactionInstance.objects.filter(
            user=user,
            reaction_type=reaction_type.value,
            reaction__comment=comment
            ).exists()

    return False
