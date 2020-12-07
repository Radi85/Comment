import os

__version__ = '2.5.1'


def _get_version():
    _parent_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(_parent_project_dir, 'VERSION')) as version_file:
        version = version_file.read().strip()

    if version.lower().startswith('v'):
        version = version[1:]

    return version


def check_release():
    release = None
    try:
        release = _get_version()
    except (FileNotFoundError, Exception):
        pass
    if release:
        assert release == __version__, 'Current version does not match with manifest VERSION'


check_release()


default_app_config = 'comment.apps.CommentConfig'
