from unittest.mock import patch, mock_open

from django.test import TestCase

from comment import _get_version


class TestGetVersion(TestCase):
    def test_when_versions_startswith_v(self):
        with patch('builtins.open', mock_open(read_data='v2.0.0'), create=True):
            self.assertEqual('2.0.0', _get_version())

    def test_when_versions_does_not_startwith_v(self):
        with patch('builtins.open', mock_open(read_data='2.0.0'), create=True):
            self.assertEqual('2.0.0', _get_version())
