from unittest.mock import patch, mock_open

import pytest

from comment import _get_version


@pytest.mark.parametrize('version, expected', [
    ('v2.0.0', '2.0.0'),
    ('2.0.0', '2.0.0'),
])
def test_get_version(version, expected):
    with patch('builtins.open', mock_open(read_data=version), create=True):
        assert _get_version() == expected
