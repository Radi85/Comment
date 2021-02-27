import re

from django import template

from comment.models import ReactionInstance, FlagInstance, Follower
from comment.forms import CommentForm
from comment.utils import (
    is_comment_moderator, is_comment_admin, get_gravatar_img, get_profile_instance, get_wrapped_words_number
)
from comment.managers import FlagInstanceManager
from comment.messages import ReactionError
from comment.context import DABContext

MULTIPLE_NEW_LINE_RE = re.compile(r'(.*)(\n){2,}(.*)')
SINGLE_NEW_LINE_RE = re.compile(r'(.*)(\n)(.*)')
register = template.Library()


@register.simple_tag(name='get_model_name')
def get_model_name(obj):
    """ returns the model name of an object """
    return type(obj).__name__


@register.simple_tag(name='get_app_name')
def get_app_name(obj):
    """ returns the app name of an object """
    return type(obj)._meta.app_label


@register.simple_tag(name='get_username_for_comment')
def get_username_for_comment(comment):
    return comment.get_username()


@register.simple_tag(name='get_profile_url')
def get_profile_url(obj):
    """ returns profile url of user """
    if not obj.user:
        return get_gravatar_img(obj.email)
    profile = get_profile_instance(obj.user)
    if profile:
        return profile.get_absolute_url()
    return get_gravatar_img(obj.email)


@register.simple_tag(name='get_img_path')
def get_img_path(obj):
    """ returns url of profile image of a user """
    profile = get_profile_instance(obj.user)
    if not profile:
        return get_gravatar_img(obj.email)
    for field in profile.__class__._meta.get_fields():
        if hasattr(field, 'upload_to'):
            return field.value_from_object(profile).url
    return get_gravatar_img(obj.email)


@register.simple_tag(name='get_comments_count')
def get_comments_count(obj, user):
    return obj.comments.all_comments_by_object(obj, include_flagged=is_comment_moderator(user)).count()


@register.simple_tag(name='get_comment_replies')
def get_comment_replies(comment, user):
    return comment.replies(include_flagged=is_comment_moderator(user))


@register.simple_tag(name='get_replies_count')
def get_replies_count(comment, user):
    return comment.replies(include_flagged=is_comment_moderator(user)).count()


def render_comments(obj, request, oauth=False):
    """
    Retrieves list of comment related to a certain object and renders the appropriate template
    """
    context = DABContext(request, model_object=obj)
    context.update({
        'comment_form': CommentForm(request=request),
        'oauth': oauth
    })
    return context


register.inclusion_tag('comment/base.html')(render_comments)


def render_content(comment, number=None):
    try:
        number = int(number)
    except (ValueError, TypeError):
        number = get_wrapped_words_number()

    # Restrict 2 or more line breaks to 2 <br>
    content = MULTIPLE_NEW_LINE_RE.sub(r'\1<br><br>\3', comment.content)
    content = SINGLE_NEW_LINE_RE.sub(r'\1<br>\3', content)
    content_words = content.split()
    if not number or len(content_words) <= number:
        text_1 = content
        text_2 = None
    else:
        text_1 = ' '.join(content_words[:number])
        text_2 = ' '.join(content_words[number:])

    return {
        'text_1': text_1,
        'text_2': text_2,
        'urlhash': comment.urlhash
    }


@register.simple_tag(name='can_delete_comment')
def can_delete_comment(comment, user):
    return is_comment_admin(user) or (comment.is_flagged and is_comment_moderator(user))


register.inclusion_tag('comment/comments/content.html')(render_content)


@register.simple_tag(name='include_static')
def include_static():
    """ This function shall be deprecated """
    return ''


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
    """
    if user.is_authenticated:
        reaction_type = getattr(ReactionInstance.ReactionType, reaction.upper(), None)
        if not reaction_type:
            raise template.TemplateSyntaxError(ReactionError.TYPE_INVALID.format(reaction_type=reaction))
        return ReactionInstance.objects.filter(
            user=user,
            reaction_type=reaction_type.value,
            reaction__comment=comment
            ).exists()

    return False


@register.filter(name='has_flagged')
def has_flagged(user, comment):
    if user.is_authenticated:
        return FlagInstance.objects.filter(user=user, flag__comment=comment).exists()

    return False


@register.filter(name='has_followed')
def has_followed(user, model_object):
    if user.is_authenticated:
        return Follower.objects.is_following(user.email, model_object)
    return False


@register.simple_tag(name='render_flag_reasons')
def render_flag_reasons():
    return FlagInstanceManager.reasons_list
