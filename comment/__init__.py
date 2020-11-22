import os


def _get_version():
    _parent_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(_parent_project_dir, 'VERSION')) as version_file:
        version = version_file.read().strip()

    if version.lower().startswith('v'):
        version = version[1:]

    return version


__version__ = _get_version()
default_app_config = 'comment.apps.CommentConfig'
