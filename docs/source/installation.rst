Installation
============

Requirements:
"""""""""""""

    1. **django-widget-tweaks==1.4.2**
    2. **Bootstrap 4.1.1**
    3. **jQuery 3.2.1**



Installation:
"""""""""""""

Installation is available via ``pip``

::

    $ pip install django-comments-dab

or via source on github

::

    $ git clone https://github.com/radi85/Comment.git
    $ cd Comment
    $ python setup.py install

Add ``comment`` to your installed_apps in your ``settings.py`` file. It
should be added after ``django.contrib.auth``:

.. code:: python

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        ...
        'comment',
        ..
    )

In your urls.py:

.. code:: python

    urlpatterns = patterns('',
        ...
        path('comment/', include('comment.urls')),
        ...
    )

Migrations for Django 2.0 and later
"""""""""""""""""""""""""""""""""""

Migrate comments:

::

    $ python manage.py migrate comment
