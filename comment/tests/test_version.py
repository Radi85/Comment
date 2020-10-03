from unittest import skipIf
from unittest.mock import patch

from django.test import TestCase

from comment import __version__, _get_version, check_release


SKIP = False
try:
    MANIFEST_VERSION = _get_version()
except FileNotFoundError:
    SKIP = True


class TestVersion(TestCase):

    @skipIf(SKIP, 'Test skipped: development purpose only')
    def test_get_version(self):
        self.assertEqual(_get_version(), MANIFEST_VERSION)

    @skipIf(SKIP, 'Test skipped: development purpose only')
    def test_manifest_matches_init_version(self):
        self.assertEqual(__version__, MANIFEST_VERSION)

    @patch('comment._get_version', side_effect=[FileNotFoundError])
    def test_check_release_file_not_found(self, mocked_get_version):
        self.assertIsNone(check_release())
        mocked_get_version.assert_called_once()

    @skipIf(SKIP, 'Test skipped: development purpose only')
    @patch('comment.__version__', return_value='not_match')
    def test_check_release_raise_assertion_error_when_versions_does_not_match(self, _):
        self.assertRaises(AssertionError, check_release)

    def test_check_release_exit_with_no_error(self):
        self.assertIsNone(check_release())
