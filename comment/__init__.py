import os

__version__ = '2.7.1'


def _get_version():
    parent_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(parent_project_dir, 'VERSION')) as version_file:
        version = version_file.read().strip().strip('v')

    return version


def check_release():
    try:
        release = _get_version()
    except FileNotFoundError:
        return

    assert release == __version__, 'Current version does not match with manifest VERSION'


check_release()


default_app_config = 'comment.apps.CommentConfig'
