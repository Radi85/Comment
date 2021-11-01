from unittest.mock import patch

from django.test import SimpleTestCase
from django.core import checks

from comment.checks import check_orders_unique, check_order_values
from comment.conf import settings


class CheckOrdersUniqueTest(SimpleTestCase):
    def test_success(self):
        order = ['-reaction__likes']

        with patch.object(settings, 'COMMENT_ORDER_BY', order):
            self.assertListEqual(check_orders_unique(None), [])

    def test_duplicate_value_raises_exception(self):
        order = ['-posted', 'posted']

        with patch.object(settings, 'COMMENT_ORDER_BY', order):
            self.assertListEqual(
                check_orders_unique(None),
                [
                    checks.Error(
                        'COMMENT_ORDER_BY should not have duplicate values.',
                        hint="Duplicated Value(s): ['-posted']. Please use one value only E.g. 'posted' or '-posted'.",
                        id='comment.E001',
                    )
                ]
            )


class CheckOrderValuesTest(SimpleTestCase):
    def test_success(self):
        order = ['-reaction__likes']

        with patch.object(settings, 'COMMENT_ORDER_BY', order):
            self.assertListEqual(check_order_values(None), [])

    def test_incorrect_value_raises_exception(self):
        order = ['err']

        with patch.object(settings, 'COMMENT_ORDER_BY', order):
            self.assertListEqual(
                check_order_values(None),
                [
                    checks.Error(
                        "'err' is not a valid value for COMMENT_ORDER_BY.",
                        hint=(
                            "Please choose one among ["
                            "'reaction__likes', 'reaction__dislikes', 'posted', "
                            "'-reaction__likes', '-reaction__dislikes', '-posted', "
                            "'?']."
                        ),
                        id='comment.E002',
                    ),
                ]
            )
