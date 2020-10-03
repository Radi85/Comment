from django import template

from comment.models import ReactionInstance, FlagInstance
from comment.forms import CommentForm
from comment.utils import (
    get_comment_context_data, is_comment_moderator, is_comment_admin, get_gravatar_img, get_profile_instance
)
from comment.managers import FlagInstanceManager
from comment.conf import settings
from comment.messages import ReactionError

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
    if not comment.user:
        if settings.COMMENT_USE_EMAIL_FIRST_PART_AS_USERNAME:
            return comment.email.split('@')[0]
        return settings.COMMENT_ANONYMOUS_USERNAME
    return comment.user.username


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
    context = get_comment_context_data(request, model_object=obj)
    context.update({
        'comment_form': CommentForm(request=request),
        'oauth': oauth
    })
    return context


register.inclusion_tag('comment/base.html')(render_comments)


def render_content(comment, number):
    number = int(number)
    content = comment.content
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


@register.simple_tag(name='render_flag_reasons')
def render_flag_reasons():
    return FlagInstanceManager.reasons_list
