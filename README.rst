.. image:: https://img.shields.io/pypi/pyversions/django-comments-dab.svg
    :target: https://pypi.python.org/pypi/django-comments-dab/
    :alt: python

.. image:: https://img.shields.io/pypi/djversions/django-comments-dab.svg
    :target: https://pypi.python.org/pypi/django-comments-dab/
    :alt: django

.. image:: https://coveralls.io/repos/github/Radi85/Comment/badge.svg
    :target: https://coveralls.io/github/Radi85/Comment
    :alt: coverage

.. image:: https://travis-ci.org/Radi85/Comment.svg?branch=develop
    :target: https://travis-ci.org/Radi85/Comment
    :alt: build

.. image:: https://readthedocs.org/projects/django-comment-dab/badge/?version=latest
    :target: https://django-comment-dab.readthedocs.io/?badge=latest
    :alt: docs

.. image:: https://img.shields.io/github/contributors/radi85/Comment
    :target: https://github.com/Radi85/Comment/graphs/contributors
    :alt: contributors

.. image:: https://img.shields.io/github/license/radi85/Comment?color=gr
    :target: https://github.com/Radi85/Comment/blob/develop/LICENSE
    :alt: licence

.. image:: https://img.shields.io/pypi/dm/django-comments-dab
    :alt: downloads

.. image:: https://badge.fury.io/py/django-comments-dab.svg
    :target: https://pypi.org/project/django-comments-dab/
    :alt: pypi

.. image:: https://img.shields.io/github/v/tag/radi85/Comment?color=gr
    :target: https://github.com/Radi85/Comment/releases
    :alt: tag

.. image:: https://img.shields.io/github/release-date/radi85/comment?color=blue
    :target: #
    :alt: Django-comment-dab Release Date

.. image:: https://img.shields.io/github/commits-since/radi85/comment/latest/develop
    :target: #
    :alt: Commits since latest release for a branch develop


===================
django-comments-dab
===================

Thanks https://www.pythonanywhere.com/

**Here is a** live_ **demo**

.. _live: https://rmustafa.pythonanywhere.com/

Full Documentation_

.. _Documentation: https://django-comment-dab.readthedocs.io/


    .. image:: https://github.com/radi85/comment/blob/develop/docs/_static/img/comment.gif


Content:

* Introduction_
* Installation_
* Setup_
* Usage_
* Example_

.. _Introduction:

Introduction
============

**dab stands for Django-Ajax-Bootstrap**
PS: Ajax and JQuery are not used anymore since v2.0.0 Vanilla JS and fetch API is used instead.

``django-comments-dab`` is a commenting application for Django-powered websites.

It allows you to integrate commenting functionality with any model you have e.g. blogs, pictures, video etc…

*List of actions that can be performed:*

    1. Post a new comment. (v2.0.0 authenticated and anonymous users)

    2. Reply to an existing comment. (v2.0.0 authenticated and anonymous users)

    3. Edit a comment. (authenticated user `comment owner`)

    4. Delete a comment. (authenticated user `comment owner` and admins)

    5. React to a comment. (authenticated users) Available reactions are LIKE and DISLIKE  # open PR if you would like to have more reactions

    6. Report (flag) a comment. (authenticated users)

    7. Delete flagged comment. (admins and moderators)

    8. Resolve or reject flag. This is used to revoke the flagged comment state (admins and moderators)

    9. Follow and unfollow thread. (authenticated users)

- All actions are done by Fetch API since V2.0.0

- Bootstrap 4.1.1 is used in comment templates for responsive design.

.. _Installation:

Installation
============

Requirements:
-------------

    1. **django>=2.1**
    2. **djangorestframework**  # only for the API Framework
    3. **Bootstrap 4.1.1**


Installation:
-------------


Installation is available via ``pip``

::

    $ pip install django-comments-dab


or via source on github

::

    $ git clone https://github.com/radi85/Comment.git
    $ cd Comment
    $ python setup.py install


Comment Settings and urls:
--------------------------

    1. Add ``comment`` to installed_apps in the ``settings.py`` file. It should be added after ``django.contrib.auth``.
    2. ``LOGIN_URL`` shall be defined in the settings.

``settings.py`` should look like this:

.. code:: python

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        ...
        'comment',
        ..
    )

    LOGIN_URL = 'login'  # or actual url

In ``urls.py``:

.. code:: python

    urlpatterns = patterns(
        path('admin/', admin.site.urls),
        path('comment/', include('comment.urls')),
        ...
        path('api/', include('comment.api.urls')),  # only required for API Framework
        ...
    )

Migrations:
-----------

Migrate comment app:

::

    $ python manage.py migrate comment


.. _Setup:

Setup
=====

Step 1 - Connecting comment model with the target model
-------------------------------------------------------

In models.py add the field ``comments`` as a ``GenericRelation`` field to the required model.

PS: Please note that the field name must be ``comments`` **NOT** ``comment``.

E.g. ``Post`` model, as shown below:

.. code:: python

    from django.contrib.contenttypes.fields import GenericRelation

    from comment.models import Comment

    class Post(models.Model):
        author = models.ForeignKey(User)
        title = models.CharField(max_length=200)
        body = models.TextField()
        # the field name should be comments
        comments = GenericRelation(Comment)

Step 2 - Adding template tags:
------------------------------

``render_comments`` *tag uses 2 required and 1 optional args*:

    1. Instance of the targeted model. (**Required**)
    2. Request object. (**Required**)
    3. oauth. (optional - Default is false)


.. _Usage:

Usage
=====

1. Basics usage:
----------------

``include_bootstrap`` tag is for bootstrap-4.1.1, if it’s already used in the project, get rid of this tag.

In the template (e.g. post_detail.) add the following template tags where ``obj`` is the instance of post model.

.. code:: jinja

    {% load comment_tags %}  {# Loading the template tag #}
    {% render_comments obj request %}  {# Render all the comments belong to the passed object "obj" #}
    {% include_bootstrap %} {# Include bootstrap 4.1.1 - remove this line if BS is already used in your project #}


2. Advanced usage:
------------------

For advanced usage and other documentation, you may read the Documentation_ or look at the docs_ directory in the repository.

.. _docs: https://github.com/Radi85/Comment/tree/develop/docs

.. _Example:

Example
========

You can play with the example app using local virtual environment

.. code:: bash

    $ git clone https://github.com/Radi85/Comment.git  # or clone your forked repo
    $ cd Comment
    $ python3 -m venv local_env  # or any name. local_env is in .gitignore
    $ export DEBUG=True
    $ source local_env/bin/activate
    $ pip install -r test/example/requirements.txt
    $ python manage.py migrate
    $ python manage.py create_initial_data
    $ python manage.py runserver


Or run with docker

.. code:: bash

    $ git clone https://github.com/Radi85/Comment.git  # or clone your forked repo
    $ cd Comment
    $ docker-compose up


Login with:

    username: ``test``

    password: ``test``

The icons are picked from Feather_. Many thanks to them for the good work.

.. _Feather: https://feathericons.com


Email's HTML template is used from https://github.com/leemunroe/responsive-html-email-template

Contributing
============

For contributing, please see the instructions at Contributing_

.. _Contributing: https://github.com/Radi85/Comment/blob/develop/CONTRIBUTING.rst
