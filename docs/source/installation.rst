Installation
============

Requirements:
-------------

    1. **django>=2.1**
    2. **djangorestframework**  # only for API Framework
    3. **Bootstrap 4.1.1**
    4. **jQuery 3.2.1**


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

    1. Add ``comment`` to your installed_apps in your ``settings.py`` file. It should be added after ``django.contrib.auth``.
    2. ``LOGIN_URL`` shall be defined in the settings.

your ``settings.py`` should look like the following:

.. code:: python

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        ...
        'comment',
        ..
    )

    LOGIN_URL = 'login'  # or your actual url

In your ``urls.py``:

.. code:: python

    urlpatterns = patterns(
        path('admin/', admin.site.urls),
        path('comment/', include('comment.urls')),
        ...
        path('api/', include('comment.api.urls')),  # only for API Framework
        ...
    )

Migrations:
-----------

Migrate comment app:

::

    $ python manage.py migrate comment
