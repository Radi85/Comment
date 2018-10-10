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


|


Templates and block tags names with default BS classes:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


**base.html**

.. code:: html

    {% block pagination %}
    {% include 'comment/pagination.html' with active_btn='bg-success' text_style='text-success' li_cls='page-item rounded mx-1' %}
    {% endblock pagination %}

|

**comment_modal.html**

.. code:: html

    {% block title %}
    Confirm comment deletion
    {% endblock title %}

    {% block content %}
    Are you sure you want to delete this comment
    {% endblock content %}

    {% block close_btn_cls %}
    btn btn-secondary
    {% endblock close_btn_cls %}


    {% block del_btn_cls %}
    btn btn-danger
    {% endblock del_btn_cls %}

|

**content.html**

.. code:: html

    {% block text_space %}
    col-10 col-md-11
    {% endblock text_space %}

    {% block c_text_cls %}
    h6 mb-0
    {% endblock c_text_cls %}

    {% block user_name %}
    {% endblock user_name %}


    {% block edit_link_cls %}
    {% endblock edit_link_cls %}

    {% block delete_btn_cls %}
    btn btn-link
    {% endblock delete_btn_cls %}

    {% block reply_link_cls %}
    ml-1
    {% endblock reply_link_cls %}


|

**image.html**

.. code:: html

    {% block pic_space %}
    col-2 col-md-1
    {% endblock pic_space %}

    {% block img_cls %}
    w-100
    {% endblock img_cls %}

|

**create_comment.html**

.. code:: html

    {% block c_form_space %}
    col-sm-9 col-md-10 px-2 m-2 m-sm-0
    {% endblock c_form_space %}

    {% block post_btn_space %}
    col-sm-3 col-md-2 px-2 m-3 m-sm-0
    {% endblock post_btn_space %}

    {% block post_btn_cls %}
    btn btn-outline-success btn-block btn-sm
    {% endblock post_btn_cls %}

    {% block oauth %}
    {% if oauth %}
    <a class="mx-1 my-0 h4 github-color" href="{% url 'social:begin' 'github' %}?next={{request.path}}"><i class="fa fa-github-square"></i></a>
    <a class="mx-1 my-0 h4 facebook-color" href="{% url 'social:begin' 'facebook' %}?next={{request.path}}"><i class="fa fa-facebook-square"></i></a>
    <a class="mx-1 my-0 h4 twitter-color" href="{% url 'social:begin' 'twitter' %}?next={{request.path}}"><i class="fa fa-twitter-square"></i></a>
    <a class="mx-1 my-0 h4 google-color" href="{% url 'social:begin' 'google-oauth2' %}?next={{request.path}}"><i class="fa fa-google-plus-square"></i></a>
    {% endif %}
    {% endblock oauth %}


|

2- CSS file:
~~~~~~~~~~~~

If you want to customize the default style of comments app , you can do the following steps:
    1. Create a ``comment.css`` file inside your ``static/css`` directory.
    2. The new created file will override the original file used in the app.
