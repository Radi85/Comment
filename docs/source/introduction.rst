django-comments-dab
===================

.. image:: https://badge.fury.io/py/django-comments-dab.svg
    :target: https://pypi.org/project/django-comments-dab/
    :alt: pypi

.. image:: https://img.shields.io/github/v/tag/radi85/Comment?color=gr
    :target: https://github.com/Radi85/Comment/releases
    :alt: tag

.. image:: https://travis-ci.org/Radi85/Comment.svg?branch=master
    :target: https://travis-ci.org/Radi85/Comment
    :alt: build

.. image:: https://coveralls.io/repos/github/Radi85/Comment/badge.svg
    :target: https://coveralls.io/github/Radi85/Comment
    :alt: coverage

.. image:: https://img.shields.io/pypi/pyversions/django-comments-dab.svg
    :target: https://pypi.python.org/pypi/django-comments-dab/
    :alt: python

.. image:: https://img.shields.io/pypi/djversions/django-comments-dab.svg
    :target: https://pypi.python.org/pypi/django-comments-dab/
    :alt: django

.. image:: https://readthedocs.org/projects/django-comment-dab/badge/?version=latest
    :target: https://django-comment-dab.readthedocs.io/?badge=latest
    :alt: docs

.. image:: https://img.shields.io/github/contributors/radi85/Comment
    :target: https://github.com/Radi85/Comment/graphs/contributors
    :alt: contributors

.. image:: https://img.shields.io/github/license/radi85/Comment?color=gr
    :target: https://github.com/Radi85/Comment/blob/master/LICENSE
    :alt: licence

.. image:: https://img.shields.io/pypi/dm/django-comments-dab
    :alt: downloads


.. image:: ../_static/img/comment.gif

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
