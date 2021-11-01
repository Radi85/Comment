from django.core.checks import Error

from comment.conf import settings


def check_order_values(app_configs, **kwargs):
    errors = []
    preferred_orders = settings.COMMENT_ORDER_BY

    allowed_orders = _get_allowed_orders()
    for preferred_order in preferred_orders:
        if preferred_order not in allowed_orders:
            errors.append(
                Error(
                    f"'{preferred_order}' is not a valid value for COMMENT_ORDER_BY.",
                    hint=f"Please choose one among {allowed_orders}.",
                    id='comment.E002',
                )
            )
    return errors


def check_orders_unique(app_configs, **kwargs):
    errors = []
    preferred_orders = settings.COMMENT_ORDER_BY

    unique_values = set(map(lambda a: a.replace('-', ''), preferred_orders))
    if len(unique_values) != len(preferred_orders):
        duplicated_orders = list(set(preferred_orders) - unique_values)
        errors.append(
            Error(
                'COMMENT_ORDER_BY should not have duplicate values.',
                hint=(
                    "Duplicated Value(s): {duplicates}. "
                    "Please use one value only E.g. '{order}' or '-{order}'.".format(
                        duplicates=duplicated_orders,
                        order=duplicated_orders[0].replace('-', ''),
                    )
                ),
                id='comment.E001',
            ),
        )
    return errors


def _get_allowed_orders():
    allowed_orders = ['reaction__likes', 'reaction__dislikes', 'posted']
    # adds support for descending order as well
    allowed_orders.extend(list(map(lambda a: '-' + a, allowed_orders)))
    # django allows this to support random order
    allowed_orders.append('?')
    return allowed_orders
