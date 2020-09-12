Changelog
=========

2.0.0
------

- Allow commenting by unauthenticated users (Anonymous comment).
- Add permalink to comments.
- Remove JQuery from dependencies and replace it with Vanilla JS.
- Update mixins and add content type and parent id validators.
- Bug fixes.

1.6.7
------

- Add states to flag model
- Add functionality to allow comment admin or moderator to change flag state
- Extend the API to cover all GUI actions

1.6.5
------

- Add groups and permissions
- Update styling
- Make the style more customizable

1.6.1
-----

- Fix bugs

1.6.0
-----

- Add flagging system - Report a comment

1.5.0
-----

- Add reactions - (LIKE and DISLIKE)
- Restrict the requests to AJAX calls only

1.4.0
-----

- Remove unnecessary dependencies.
- Add unittests for all components.
- Add compatibility checking with django versions >= 2.1


1.3.0
-----

- For more compatibility with ContentType (models), slug option has been deprecated.
- Now retrieving and creating comment is based on provided ContentType and its id only.


1.2.4
-----

- Integrate profile fields with user serializer



1.2.3
-----

- Change the retrieved comments list in the API from all comments to list of comments and associated replies to a given content type and object ID



1.2.2
-----

- Update pagination on comment action


1.2.1
-----

- Fix static files bug


1.2.0
-----

- Serialize comments
- Add web API feature


1.1.0
-----

- Add pagination feature


1.0.1
-----

- Move profile_model_name and profile_app_name to setting file
- Fix a bug due to letter case in ContentType class




1.0.0
-----

First release
