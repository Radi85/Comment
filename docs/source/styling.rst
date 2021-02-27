Style Customization
====================

Some actual customizations has been done in the example_ project

.. _example: https://github.com/Radi85/Comment/tree/master/test/example

1- Templates and default blocks:
--------------------------------

BS classes, pagination and some other template values can be now customized from within your templates directory as follows:

    1. Create ``comment`` folder inside templates directory.

    2. Create a new template file ``.html`` give it the same name of the default template that needs to be overridden and put it in the right directory.

    **Templates tree:**

    .. code:: bash

        comment
        └── templates
            └── comment
                ├── anonymous
                │   ├── confirmation_request.html
                │   ├── confirmation_request.txt
                │   └── discarded.html
                ├── comments
                │   ├── apply_icon.html
                │   ├── base.html
                │   ├── cancel_icon.html
                │   ├── child_comment.html
                │   ├── comment_body.html
                │   ├── comment_content.html
                │   ├── comment_form.html
                │   ├── comment_modal.html
                │   ├── content.html
                │   ├── create_comment.html
                │   ├── delete_icon.html
                │   ├── edit_icon.html
                │   ├── messages.html
                │   ├── pagination.html
                │   ├── parent_comment.html
                │   ├── reject_icon.html
                │   ├── resolve_icon.html
                │   ├── three_dots_menu.html
                │   ├── update_comment.html
                │   └── urlhash.html
                ├── email
                │   ├── email_template.html
                │   └── footer.html
                ├── flags
                │   ├── flag_icon.html
                │   ├── flag_modal.html
                │   └── flags.html
                ├── follow
                │   ├── follow.html
                │   ├── follow_icon.html
                │   └── follow_modal.html
                ├── notifications
                │   ├── notification.html
                │   └── notification.txt
                ├── reactions
                │   ├── dislike_icon.html
                │   ├── like_icon.html
                │   └── reactions.html
                ├── base.html
                ├── bootstrap.html
                └── static.html



for example to override the BS classes of `submit buttons` and pagination style do the following:

    create ``templates/comment/comments/create_comment.html``

    .. code:: jinja

        {% extends "comment/comments/create_comment.html" %}

        {% block submit_button_cls %}
        btn btn-primary btn-block btn-sm
        {% endblock submit_button_cls %}

        {# override pagination style: #}
        {% block pagination %}
        {% include 'comment/comments/pagination.html' with active_btn='bg-danger' text_style='text-dark' li_cls='page-item rounded mx-1' %}
        {% endblock pagination %}


Templates and block tags names with default values:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This style customization is compatible with version >= **1.6.5**
Some block tags may not work on old versions.

**base.html**

.. code:: jinja

    {% extends "comment/comments/base.html" %}

    {% block comment_section_cls %}my-5 mx-3{% endblock comment_section_cls %}

    {% block header_div_cls %}border-bottom mb-4{% endblock header_div_cls %}
    {% block header_title_cls %}bb{% endblock header_title_cls %}
    {% block follow_icon_wrapper_cls %}float-right{% endblock follow_icon_wrapper_cls %}

    {% block pagination %}  {# override default pagination classes #}
    {% include 'comment/comments/pagination.html' with active_btn='bg-success' text_style='text-success' li_cls='page-item rounded mx-1' %}
    {% endblock pagination %}


**create_comment.html**

.. code:: jinja

    {% extends "comment/comments/create_comment.html" %}

    {% block text_area_wrapper_cls %}col-sm-9 col-md-10 px-2 m-2 m-sm-0{% endblock text_area_wrapper_cls %}
    {% block submit_button_wrapper_cls %}col-sm-3 col-md-2 px-2 m-3 m-sm-0{% endblock submit_button_wrapper_cls %}
    {% block submit_button_cls %}btn btn-outline-success btn-block btn-sm{% endblock submit_button_cls %}

    {% block login_info %}
    {# Please see 'comment/comments/create_comment.html' template for default block #}
    {% endblock login_info %}

    {% block oauth %}  {# override default oauth urls section #}
    <a class="mx-1 my-0 h4 github-color" href="{% url 'social:begin' 'github' %}?next={{request.path}}"><i class="fa fa-github-square"></i></a>
    <a class="mx-1 my-0 h4 facebook-color" href="{% url 'social:begin' 'facebook' %}?next={{request.path}}"><i class="fa fa-facebook-square"></i></a>
    <a class="mx-1 my-0 h4 twitter-color" href="{% url 'social:begin' 'twitter' %}?next={{request.path}}"><i class="fa fa-twitter-square"></i></a>
    <a class="mx-1 my-0 h4 google-color" href="{% url 'social:begin' 'google-oauth2' %}?next={{request.path}}"><i class="fa fa-google-plus-square"></i></a>
    {% endblock oauth %}


**parent_comment.html**

.. code:: jinja

    {% extends "comment/comments/parent_comment.html" %}

    {% block parent_comment_wrapper_cls %}text-wrap{% endblock parent_comment_wrapper_cls %}
    {% block replies_wrapper_cls %}ml-5 my-4{% endblock replies_wrapper_cls %}


**child_comment.html**

.. code:: jinja

    {% extends "comment/comments/child_comment.html" %}

    {% block child_comment_wrapper_cls %}text-wrap mb-4{% endblock child_comment_wrapper_cls %}


**comment_body.html**

.. code:: jinja

    {% extends "comment/comments/comment_body.html" %}

    {% block image_wrapper_cls %}col-2 col-md-1{% endblock image_wrapper_cls %}
    {% block image_cls %}w-100{% endblock image_cls %}

    {% block three_dots_wrapper_cls %}col-1{% endblock three_dots_wrapper_cls %}


**comment_content.html**

.. code:: jinja

    {% extends "comment/comments/comment_content.html" %}

    {% block content_wrapper_cls %}{% if has_valid_profile %}col-9 col-md-10{% else %}co-11 mx-3{% endif %}{% endblock content_wrapper_cls %}
    {% block comment_content %}   {# override truncate words number - change the number 30 to your desired or 0 if you don't want to fold the comment #}
        {# new settings variable COMMENT_WRAP_CONTENT_WORDS is introduce for changing the number of wrapped words. #}
        {# working with the settings var is more convenient than overriding the template #}
        {% render_content comment words_number %}  {# words_number is the settings variable COMMENT_WRAP_CONTENT_WORDS #}
    {% endblock comment_content %}

    {% block footer_wrapper_cls %}mt-2 text-muted{% endblock footer_wrapper_cls %}
    {% block username_cls %}{% endblock username_cls %}
    {% block reply_count_cls %}text-dark{% endblock reply_count_cls %}
    {% block reply_link_cls %}btn btn-link ml-1{% endblock reply_link_cls %}
    {% block follow_icon_wrapper_cls %}d-inline ml-3{% endblock follow_icon_wrapper_cls %}


**content.html**

.. code:: jinja

    {% extends "comment/comments/content.html" %}

    {% block content_text_cls %}mb-0{% endblock content_text_cls %}
    {% block read_more_cls %}btn btn-link btn-xs read-more{% endblock read_more_cls %}


**edit_icon.html**

.. code:: jinja

    {% extends "comment/comments/edit_icon.html" %}

    {% block edit_link_cls %}btn btn-link{% endblock edit_link_cls %}
    {% block edit_img_icon %}Here comes your favorite icon{% endblock edit_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block edit_icon_color %}#00bc8c{% endblock edit_icon_color %}


**delete_icon.html**

.. code:: jinja

    {% extends "comment/comments/delete_icon.html" %}

    {% block delete_btn_cls %}btn btn-link{% endblock delete_btn_cls %}
    {% block delete_img_icon %}Here comes your favorite icon{% endblock delete_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block delete_icon_color %}#E74C3C{% endblock delete_icon_color %}


**apply_icon.html**

.. code:: jinja

    {% extends "comment/comments/apply_icon.html" %}

    {% block apply_btn_cls %}btn btn-link{% endblock apply_btn_cls %}
    {% block apply_img_icon %}Here comes your favorite icon{% endblock apply_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block apply_icon_color %}#00bc8c{% endblock apply_icon_color %}


**cancel_icon.html**

.. code:: jinja

    {% extends "comment/comments/cancel_icon.html" %}

    {% block cancel_btn_cls %}btn btn-link{% endblock cancel_btn_cls %}
    {% block cancel_img_icon %}Here comes your favorite icon{% endblock cancel_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block cancel_icon_color %}#E74C3C{% endblock cancel_icon_color %}


**flag_icon.html**

.. code:: jinja

    {% extends "comment/flags/flag_icon.html" %}

    {% block flag_img_icon %}
        {#
        IMPORTANT: please consider adding these classes to your icon element as they are used in JS
        class="comment-flag-icon {% if user|has_flagged:comment %}user-has-flagged{% else %}user-has-not-flagged{% endif %}"
        #}
        Here comes your favorite icon
    {% endblock flag_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block flag_icon_color %}#427297{% endblock flag_icon_color %}


**like_icon.html**

.. code:: jinja

    {% extends "comment/actions/like_icon.html" %}

    {% block like_img_icon %}
        {% load comment_tags %}
        {% has_reacted user=user comment=comment reaction="like" as has_user_liked %}
        {#
        IMPORTANT: please consider adding these classes to your icon element as they are used in JS
        class="comment-reaction-icon reaction-like {% if has_user_liked %}user-has-reacted{% else %}user-has-not-reacted{% endif %}"
        #}
        Here comes your favorite icon
    {% endblock like_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block like_icon_color %}#427297{% endblock like_icon_color %}


**dislike_icon.html**

.. code:: jinja

    {% extends "comment/comments/reject_icon.html" %}

    {% block dislike_img_icon %}
        {% load comment_tags %}
        {% has_reacted user=user comment=comment reaction="dislike" as has_user_disliked %}
        {#
        IMPORTANT: please consider adding these classes to your icon element as they are used in JS
        class="comment-reaction-icon reaction-dislike {% if has_user_disliked %}user-has-reacted{% else %}user-has-not-reacted{% endif %}"
        #}
        Here comes your favorite icon
    {% endblock dislike_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block dislike_icon_color %}#427297{% endblock dislike_icon_color %}


**reject_icon.html**

.. code:: jinja

    {% extends "comment/comments/reject_icon.html" %}

    {% block reject_img_icon %}}
        {#
        IMPORTANT: please consider adding this class to your icon element as it is used in JS
        class="{% if comment.has_rejected_state %}flag-rejected{% endif %}"
        #}
        Here comes your favorite icon
    {% block reject_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block reject_icon_color %}#427297{% endblock reject_icon_color %}


**resolve_icon.html**

.. code:: jinja

    {% extends "comment/comments/resolve_icon.html" %}

    {% block resolved_img_icon %}}
        {#
        IMPORTANT: please consider adding this class to your icon element as it is used in JS
        class="{% if comment.has_resolved_state %}flag-resolved{% endif %}"
        #}
        Here comes your favorite icon
    {% block resolved_img_icon %}

    {# use this tag for overriding the default icon color, this tag won't have effect in case of using the above one #}
    {% block resolved_icon_color %}#427297{% endblock resolved_icon_color %}


**follow_icon.html**

.. code:: jinja

    {% extends "comment/follow/follow_icon.html" %}

    {% block follow_img_icon %}
        {#
        IMPORTANT: please consider adding these classes to your icon element as they are used in JS
        class="comment-follow-icon {% if user|has_followed:model_object %}user-has-followed{% endif %}"
        #}
        Here comes your favorite icon
    {% endblock follow_img_icon %}


**comment_modal.html**

.. code:: jinja

    {% extends "comment/comments/comment_modal.html" %}

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


**flag_modal.html**

.. code:: jinja

    {% extends "comment/flags/flag_modal.html" %}

    {% block title %}
    {% trans "Please select a reason for flagging" %}
    {% endblock title %}

    {% block flag_link_cls %}{% endblock flag_link_cls %}


**follow_modal.html**

.. code:: jinja

    {% extends "comment/follow/follow_modal.html" %}

    {% block title %}
    {% trans "Please insert your email to follow this thread" %}
    {% endblock title %}

    {% block email_input %}
        <div class="row">
            <div class="col-3">
                <label for="email">Email:</label>
            </div>
            <div class="col-9">

                <input id="email" class="form-control mr-2 w-100" type="email" name="email" required>
                <div class="error text-danger small mt-1"></div>
            </div>
        </div>
    {% endblock email_input %}

    {% block follow_btn_extra_cls %}{% endblock follow_btn_extra_cls %}


Email templates:
^^^^^^^^^^^^^^^^^

Responsive email templates are used from https://github.com/leemunroe/responsive-html-email-template

This can be overridden by creating ``base.html`` in `templates/comment/email/` directory.

Both ``confirmation_request.html`` and ``notification.html`` extends the base email template and they have the following blocks
for partial customization:

.. code:: jinja

    {% extends "comment/notifications/notification.html" %}

    {% block content %}
    {# your custom email message/template here #}
    {% endblock content %}

    {% block footer %}
    {# your footer here #}
    {% endblock footer %}

PS: The footer template is disabled by default.

2- CSS file:
------------

To customize the default style of comments app , you can create a ``comment.css`` file inside ``static/css`` directory.

The new created file will override the original file used in the app.
