Installation
------------


Requirements:
~~~~~~~~~~~~~

    1. **django>=2.1.5**
    2. **django-widget-tweaks==1.4.2**
    3. **djangorestframework==3.8.2**  # for API Framework
    4. **Bootstrap 4.1.1**
    5. **jQuery 3.2.1**


Installation:
~~~~~~~~~~~~~


Installation is available via ``pip``

::

    $ pip install django-comments-dab


or via source on github

::

    $ git clone https://github.com/radi85/Comment.git
    $ cd Comment
    $ python setup.py install


Settings and urls:
~~~~~~~~~~~~~~~~~~

    1. Add ``comment`` to your installed_apps in your ``settings.py`` file. It should be added after ``django.contrib.auth``. and,
    2. Make sure that ``widget-tweaks`` is already included in installed_apps as well.
    3. ``LOGIN_URL`` shall be defined in the settings.

your ``settings.py`` should look like the following:

.. code:: python

    INSTALLED_APPS = (
        'django.contrib.admin',
        'django.contrib.auth',
        ...
        'widget_tweaks',
        'comment',
        'rest_framework',  # for API Framework
        ..
    )

    LOGIN_URL = 'login'  # or your actual url

In your urls.py:

.. code:: python

    urlpatterns = patterns(
        path('admin/', admin.site.urls),
        path('comment/', include('comment.urls')),
        ...
        path('api/', include('comment.api.urls')),  # for API Framework
        ...
    )

Migrations:
~~~~~~~~~~~

Migrate comment app:

::

    $ python manage.py migrate comment
