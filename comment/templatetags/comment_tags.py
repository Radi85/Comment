from django import template

from comment.models import ReactionInstance, FlagInstance
from comment.forms import CommentForm
from comment.utils import get_comment_context_data, get_profile_content_type, is_comment_moderator, is_comment_admin
from comment.managers import FlagInstanceManager

register = template.Library()


@register.simple_tag(name='get_model_name')
def get_model_name(obj):
    """ returns the model name of an object """
    return type(obj).__name__


@register.simple_tag(name='get_app_name')
def get_app_name(obj):
    """ returns the app name of an object """
    return type(obj)._meta.app_label


@register.simple_tag(name='get_profile_url')
def get_profile_url(obj):
    """ returns profile url of user """
    content_type = get_profile_content_type()
    if not content_type:
        return ''

    profile = content_type.get_object_for_this_type(user=obj.user)
    return profile.get_absolute_url()


@register.simple_tag(name='get_img_path')
def get_img_path(obj):
    """ returns url of profile image of a user """
    content_type = get_profile_content_type()
    if not content_type:
        return ''

    profile_model = content_type.model_class()
    fields = profile_model._meta.get_fields()
    profile = content_type.model_class().objects.get(user=obj.user)
    for field in fields:
        if hasattr(field, 'upload_to'):
            return field.value_from_object(profile).url
    return ''


@register.simple_tag(name='get_comments_count')
def get_comments_count(obj, user):
    return obj.comments.all_comments_by_object(obj, include_flagged=is_comment_moderator(user)).count()


@register.simple_tag(name='get_comment_replies')
def get_comment_replies(comment, user):
    return comment.replies(include_flagged=is_comment_moderator(user))


@register.simple_tag(name='get_replies_count')
def get_replies_count(comment, user):
    return comment.replies(include_flagged=is_comment_moderator(user)).count()


def render_comments(obj, request, oauth=False, comments_per_page=10):
    """
    Retrieves list of comment related to a certain object and renders the appropriate template
    """
    context = get_comment_context_data(request, model_object=obj, comments_per_page=comments_per_page)
    context.update({
        'comment_form': CommentForm(),
        'oauth': oauth
    })
    return context


register.inclusion_tag('comment/comments/base.html')(render_comments)


def render_content(content, number):
    number = int(number)
    content_words = content.split(' ')
    if not number or len(content_words) <= number:
        text_1 = content
        text_2 = None
    else:
        text_1 = ' '.join(content_words[:number])
        text_2 = ' '.join(content_words[number:])

    return {
        'text_1': text_1,
        'text_2': text_2
    }


@register.simple_tag(name='can_delete_comment')
def can_delete_comment(comment, user):
    return is_comment_admin(user) or (comment.is_flagged and is_comment_moderator(user))


register.inclusion_tag('comment/comments/content.html')(render_content)


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


@register.filter(name='has_flagged')
def has_flagged(user, comment):
    if user.is_authenticated:
        return FlagInstance.objects.filter(user=user, flag__comment=comment).exists()

    return False


@register.simple_tag(name='render_flag_reasons')
def render_flag_reasons():
    return FlagInstanceManager.reasons_list
