from django.utils.translation import gettext_lazy as _


class ErrorMessage:
    LOGIN_URL_MISSING = _('Comment App: LOGIN_URL is not in the settings')
    METHOD_NOT_IMPLEMENTED = _('Your {class_name} class has not defined a {method_name} method, which is required.')
    NON_AJAX_REQUEST = _('Only AJAX request are allowed')
    INVALID_ORDER_ARGUMENT = _((
        'Comment app: "{order}" is not a valid value for COMMENT_ORDER_BY. '
        'Please choose one among {allowed_orders}.'
        ))
    DUPLICATE_ORDER_VALUE = _((
        'Comment app: COMMENT_ORDER_BY should not have duplicated values '
        'Duplicated Values: {duplicates}. Please use one value only E.g. "{order}" or "-{order}".'
    ))
    WRAP_CONTENT_WORDS_NOT_INT = _('Comment App: settings var COMMENT_WRAP_CONTENT_WORDS must be an integer')


class ExceptionError:
    ERROR_TYPE = _('error')
    BAD_REQUEST = _('Bad Request')


class ContentTypeError:
    ID_NOT_INTEGER = _('{var_name} id must be an integer, {id} is NOT')
    APP_NAME_MISSING = _('app name must be provided')
    APP_NAME_INVALID = _('{app_name} is NOT a valid app name')
    MODEL_NAME_MISSING = _('model name must be provided')
    MODEL_NAME_INVALID = _('{model_name} is NOT a valid model name')
    MODEL_ID_MISSING = _('model id must be provided')
    MODEL_ID_INVALID = _('{model_id} is NOT a valid model id for the model {model_name}')
    PARENT_ID_INVALID = _('{parent_id} is NOT a valid id for a parent comment or '
                          'the parent comment does NOT belong to the provided model object')


class FlagError:
    SYSTEM_NOT_ENABLED = _('Flagging system must be enabled')
    NOT_FLAGGED_OBJECT = _('Object must be flagged!')
    STATE_INVALID = _('{state} is an invalid state')
    REASON_INVALID = _('{reason} is an invalid reason')
    INFO_MISSING = _('Please supply some information as the reason for flagging')
    ALREADY_FLAGGED_BY_USER = _('This comment is already flagged by this user ({user})')
    NOT_FLAGGED_BY_USER = _('This comment was not flagged by this user ({user})')
    REJECT_UNFLAGGED_COMMENT = _('This action cannot be applied on unflagged comments')
    RESOLVE_UNEDITED_COMMENT = _('The comment must be edited before resolving the flag')
    STATE_CHANGE_ERROR = _('Unable to change flag state at the moment!')


class ReactionError:
    TYPE_INVALID = _('Reaction must be an valid ReactionManager.RelationType. {reaction_type} is not')


class EmailError:
    EMAIL_INVALID = _('Enter a valid email address.')
    EMAIL_MISSING = _('Email is required for posting anonymous comments.')
    BROKEN_VERIFICATION_LINK = _('The link seems to be broken.')
    USED_VERIFICATION_LINK = _('The comment has already been verified.')


class FlagInfo:
    FLAGGED_SUCCESS = _('Comment flagged')
    UNFLAGGED_SUCCESS = _('Comment flag removed')


class ReactionInfo:
    UPDATED_SUCCESS = _('Your reaction has been updated successfully')


class EmailInfo:
    CONFIRMATION_SUBJECT = _('Comment Confirmation Request')
    CONFIRMATION_SENT = _('We have sent a verification link to your email.'
                          'The comment will be displayed after it is verified.')
    INPUT_PLACEHOLDER = _('email address, this will be used for verification.')
    INPUT_TITLE = _('email address, it will be used for verification.')
    NOTIFICATION_SUBJECT = _('{username} added comment to "{thread_name}"')
    LABEL = _('email')


class FlagState:
    UNFLAGGED = _('Unflagged')
    FLAGGED = _('Flagged')
    REJECTED = _('Flag rejected by the moderator')
    RESOLVED = _('Comment modified by the author')


class FollowError:
    EMAIL_REQUIRED = _('Email is required to subscribe {model_object}')
    SYSTEM_NOT_ENABLED = _('Subscribe system must be enabled')
