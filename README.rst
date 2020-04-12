.. image:: https://badge.fury.io/py/django-comments-dab.svg
    :target: https://badge.fury.io/py/django-comments-dab

.. image:: https://badge.fury.io/gh/radi85%2FComment.svg
    :target: https://badge.fury.io/gh/radi85%2FComment

.. image:: https://travis-ci.org/Radi85/Comment.svg
    :target: https://travis-ci.org/Radi85/Comment

.. image:: https://coveralls.io/repos/github/Radi85/Comment/badge.svg
    :target: https://coveralls.io/github/Radi85/Comment

.. image:: https://img.shields.io/pypi/pyversions/django-comments-dab.svg
   :target: https://pypi.python.org/pypi/django-comments-dab/

.. image:: https://img.shields.io/pypi/djversions/django-comments-dab.svg
   :target: https://pypi.python.org/pypi/django-comments-dab/

django-comments-dab
===================

**dab stands for Django-Ajax-Bootstrap**

``django-comments-dab`` is a commenting application for Django-powered
websites.

It allows you to integrate commenting functionality with any model you have e.g. blogs, pictures, video etc…

*List of actions the authenticated user can do:*

    1. Post a new comment.

    2. Reply to an existing comment.

    3. Edit a comment you posted.

    4. Delete a comment you posted.


- All actions are done by ajax calls - JQuery 3.2.1

- Bootstrap 4.1.1 is used in comment templates for responsive design.


Installation
------------

Requirements:
~~~~~~~~~~~~~

    1. **django>=2.1**
    2. **djangorestframework**  # only for API Framework
    3. **Bootstrap 4.1.1**
    4. **jQuery 3.2.1**


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


Comment Settings and urls:
~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~

Migrate comment app:

::

    $ python manage.py migrate comment



Setup
-----

Step 1 - Connecting comment model with the target model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your models.py add the field ``comments`` as a ``GenericRelation`` field to the required model.

PS: Please note that field name must be ``comments`` **NOT** ``comment``.

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``render_comments`` *tag uses 2 positional and 2 optional args*:

    1. Instance of the targeted model. (**positional**)
    2. Request object. (**positional**)
    3. oauth. (optional - Default is false)
    4. comments_per_page (number of Comments Per Page - Default is 10)


1. Basics usage:
^^^^^^^^^^^^^^^^

``include_static`` this tag will include required jquery and javascript file,
if you already use jquery please make sure it is not the slim version which doesn't support ajax.
``include_bootstrap`` tag is for bootstrap-4.1.1, if it’s already included
in your project, get rid of this tag.

In your template (e.g. post_detail.html) add the following template tags where ``obj`` is the instance of post model.

.. code:: python

    {% load comment_tags %}  # Loading the template tag
    {% render_comments obj request %}  # Render all the comments belonging to a passed object


**Include static files:**

The ``comment`` app has three template tags for static files that the app requires.
These tags need to be included in the end of your base template.


- **Case 1:** You already have jQuery in your project then the following tags shall be included below jQuery file:

.. code:: html

    {% load comment_tags %}  <!-- Loading the template tag -->

    <script src="https://code.jquery.com/jquery-3.3.1.js"></script>
    {% include_static %}  <!-- Include comment.js file only -->
    {% include_bootstrap %}  <!-- Include bootstrap-4.1.1 - remove this line if it is already used in your project -->


- **Case 2:** You don't have jQuery in your project then the following tags shall be included:

.. code:: html

    {% load comment_tags %}  <!-- Loading the template tag -->

    {% include_static_jquery %}  <!-- Include mini jQuery 3.2.1 and required js file -->
    {% include_bootstrap %}  <!-- Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project -->


2. Advanced usage:
^^^^^^^^^^^^^^^^^^

    **1. Customize or remove the pagination:**

    By default the comments will be paginated, 10 comments per page.
    To disabled the pagination pass ``comments_per_page=None``
    To change the default number, pass ``comments_per_page=number`` to ``render_comments``.

    .. code:: html

        {% load comment_tags %}  <!-- Loading the template tag -->

        {% render_comments obj request comments_per_page=5 %}  <!-- Include all the comments belonging to a certain object -->
        {% include_bootstrap %} <!-- Include bootstrap 4.1.1 - remove this line if BS 4.1.1 is already used in your project -->
        {% include_static %} <!-- Include jQuery 3.2.1 and required js file -->



    **2. Integrate existing profile app with comments app:**

    If you have a profile model for the user and you would like to show the
    profile image next to each comment, do the following steps:

    - Add ``PROFILE_APP_NAME`` and ``PROFILE_MODEL_NAME`` variables to your ``settings.py`` file.
        e.g if user profile app is called ``accounts`` and profile model is called ``UserProfile``

        ``settings.py``:

        .. code:: python

            PROFILE_APP_NAME = 'accounts'
            PROFILE_MODEL_NAME = 'UserProfile' # letter case insensitive



    - Make sure that ``get_absolute_url`` method is defined in your profile model.

        .. code:: python

            from django.urls import reverse

            class UserProfile(models.Model):
                user = models.OneToOneField(User, on_delete=models.CASCADE)
                ...
                ...

                # this method must be defined for appropriate url mapping in comments section
                def get_absolute_url(self):
                    return reverse('your_profile_url_name')


Web API
-------

django-comments-dab uses django-rest-framework to expose a Web API that provides
developers with access to the same functionality offered through the web user interface.

There are 5 methods available to perform the following actions:


    1. Post a new comment. (Authenticated)

    2. Reply to an existing comment. (Authenticated)

    3. Edit a comment you posted. (Authenticated)

    4. Delete a comment you posted. (Authenticated)

    5. Retrieve the list of comments and associated replies to a given content type and object ID.

These actions are explained below.

Setup:
~~~~~~

To integrate the comment API in your content type (e.g Post model), in ``serializers.py``
for the Post model add comments field as shown below:


.. code:: python

    from rest_framework import serializers
    from comment.models import Comment
    from comment.api.serializers import CommentSerializer


    class PostSerializer(serializers.ModelSerializer):

        comments = serializers.SerializerMethodField()

        class Meta:
            model = Post
            fields = ('id',
                      ...
                      ...
                      'comments')

        def get_comments(self, obj):
            comments_qs = Comment.objects.filter_parents_by_object(obj)
            return CommentSerializer(comments_qs, many=True).data


By default all fields in profile model will be nested inside the user object in JSON response.
This can only happen if the profile attributes are defined in your ``settings.py``.
In case you would like to serialize particular fields in the profile model you should explicitly
declare the ``COMMENT_PROFILE_API_FIELDS`` tuple inside your ``settings.py``:


.. code:: python

        PROFILE_APP_NAME = 'accounts'
        PROFILE_MODEL_NAME = 'userprofile'
        # the field names below must be similar to your profile model fields
        COMMENT_PROFILE_API_FIELDS = ('display_name', 'birth_date', 'image')


Comment API actions:
~~~~~~~~~~~~~~~~~~~~

    **1- Retrieve the list of comments and associated replies to a given content type and object ID:**

    This action can be performed by providing the url with data queries related to the content type.

    Get request accepts 3 params:


    - ``type``: is the model name of the content type that have comments associated with it.
    - ``id``: is the id of an object of that model




    For example if you are using axios to retrieve the comment list of second object (id=2) of a model (content type) called post.
    you can do the following:

    ::

        $ curl 'http://localhost:8000/api/comments/?type=TYPE&id=ID'


    **2- Post a comment or reply to an existing comment:**

    Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

    - ``parent_id``: is 0 or **NOT PROVIDED** for parent comments and for reply comments must be the id of parent comment


    Example: posting a parent comment

    ::

        $ curl -X POST -u USERNAME:PASSWORD -d "content=CONTENT" "http://localhost:8000/api/comments/create/?type=MODEL&id=ID&parent_id=0"


    **3- Update a comment:**

    Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

    This action requires the ``comment.id`` that you want to update:


    ::

        $ curl -X PUT -u USERNAME:PASSWORD -d "content=CONTENT" "http://localhost:8000/api/comments/ID/



    **4- Delete a comment:**

    Authorization must be provided as a TOKEN or USERNAME:PASSWORD.

    This action requires the ``comment.id`` that you want to delete:

    ::

        $ curl -X DELETE -u USERNAME:PASSWORD "http://localhost:8000/api/comments/ID/



Style Customize:
----------------

1- Bootstrap classes:
~~~~~~~~~~~~~~~~~~~~~

BS class used in the default template can be now customized from within your templates directory as follows:

    1. Create ``comment`` folder inside your templates directory.

    2. Create new template file ``.html`` with the same name of the default template you wish to override BS classes in it.


for example to override the BS classes of comment and reply btn do the following:

create ``templates/comment/create_comment.html``

.. code:: python

    {% extends "comment/create_comment.html" %}

    {% block post_btn_cls %}
    btn btn-primary btn-block btn-sm
    {% endblock post_btn_cls %}

`Read the Doc`_ for more info about template names and block tags name.

.. _`Read the Doc`: https://django-comment-dab.readthedocs.io/


2- CSS file:
~~~~~~~~~~~~

If you want to customize the default style of comments app , you can do the following steps:

    1. Create a ``comment.css`` file inside your ``static/css`` directory.

    2. The new created file will override the original file used in the app.
