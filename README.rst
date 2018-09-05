django-comments-dab App - v1.1.0
================================

**dab stands for Django-Ajax-Bootstrap**

``django-comments-dab`` is a commenting application for Django-powered
websites.

It allows you to integrate commenting functionality to any model you
have e.g. blogs, pictures, etc…

*List of actions you can do:*

    1. Add a comment. (Authenticated)

    2. Edit a comment you posted. (Authenticated)

    3. Delete a comment you posted. (Authenticated)


**-All actions are done by ajax - JQuery 3.2.1**

**-Bootstrap 4.1.1 is used in comment templates for responsive design.**

Installation
------------


Requirements:
~~~~~~~~~~~~~

    1. **django-widget-tweaks==1.4.2**
    2. **Bootstrap 4.1.1**
    3. **jQuery 3.2.1**


Installation:
~~~~~~~~~~~~~


Installation is available via ``pip``

``$ pip install django-comments-dab``

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Migrate comments:

::

    $ python manage.py migrate comment



Setup
-----

Step 1
~~~~~~

In your models.py add the field comments (Please note that field name
must be ``comments`` not ``comment``) to the model for which comment
should be added (e.g. Post) and the appropriate imports as shown below:

.. code:: python

    from django.contrib.contenttypes.fields import GenericRelation
    from comment.models import Comment

    class Post(models.Model):
        author = models.ForeignKey(User)
        title = models.CharField(max_length=200)
        body = models.TextField()
        # the field name should be comments
        comments = GenericRelation(Comment)

Step 2
~~~~~~

``get_comments`` *tag uses 2 positional and 3 optional args*:

    1. The instance of the model. (**positional**)
    2. Request object. (**positional**)
    3. oauth. (optional - Default is false)
    4. paginate. (optional - Default is false)
    5. cpp (number of Comments Per Page - Default is 10)


1. Basics usage:
^^^^^^^^^^^^^^^^

``include_static`` this tag will include required jquery and javascript
file. ``include_bootstrap`` for bootstrap 4.1.1 if it’s already included
in your project, get rid of this tag.

In your template (e.g. post-detail.html) add the following template tags
where object is the instance of post.

.. code:: python

    {% load comment_tags %}  # Loading the template tag
    {% get_comments object request %}  # Include all the comments belonging to a certain object
    {% include_bootstrap %} # Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project
    {% include_static %} # Include jQuery 3.2.1 and required js file



2. Advanced usage:
^^^^^^^^^^^^^^^^^^

    **1. Add pagination:**

    To add pagination to your comments, you need to pass two variables to the ``get_comments`` tag.
    ``paginate`` must be set to ``True`` and set ``cpp`` var (number of comments per page - default is 10) to the desired number of comments per page.
    e.g. If you would like to have 5 comments per page, the ``get_comments`` tag should look like this:

    .. code:: python

        {% load comment_tags %}  # Loading the template tag
        {% get_comments object request paginate=True cpp=5 %}  # Include all the comments belonging to a certain object
        {% include_bootstrap %} # Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project
        {% include_static %} # Include jQuery 3.2.1 and required js file



    **2. Integrate existing profile app with comments app:**

    If you have profile model for the user and you would like to show the
    profile image on each comment you need to assign PROFILE_APP_NAME and
    PROFILE_MODEL_NAME variables in your ``settings.py`` file. (e.g if user profile
    app is called ``accounts`` and profile model is called ``UserProfile``)
    Update your ``settings.py``:

    .. code:: python

        PROFILE_APP_NAME = 'accounts'
        PROFILE_MODEL_NAME = 'UserProfile' # letter case insensitive



Customize Styling
-----------------

If you want to customize the default style of comments app , you can do the following steps:
    1. Create a ``comment.css`` file inside your ``static/css`` directory.
    2. The new created file will overwrite the original file used in the app.

and you’re done.
