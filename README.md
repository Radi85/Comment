# django-comments-dab Comments
## dab stands for Django-Ajax-Bootstrap

`django-comments-dab` is a commenting application for Django-powered websites.

It allows you to integrate commenting functionality to any model you have eg. blogs, pictures, etc...

List of actions you can do:
#. Add a comment (Authenticated)
#. Edit a comment you posted (Authenticated)
#. Delete a comment you posted (Authenticated)

### All actions are done by ajax - Jquery 3.2.1
### Bootstrap 4.1.1 is used in comment templates for responsive design.


## Installation

Installation is available via `pip`

`$ pip install django-comments-dab`

or via source on github

```
$ git clone https://github.com/radi85/Comment.git
$ cd Comment
$ python setup.py install
```

Add `comment` to your installed_apps in your `settings.py` file. It should be added after `django.contrib.auth`:

```python
INSTALLED_APPS = (
	'django.contrib.admin',
	'django.contrib.auth',
	...
	'comment',
	..
)
```

In your urls.py:

```python
urlpatterns = patterns('',
    ...
    path('comment/', include('comment.urls')),
    ...
)
```


## Migrations for Django 2.0 and later

Migrate comments:
```
$ python manage.py migrate comment
```


## Setup

### Step 1
In your models.py add the field comments (Please note that field name must be `comments` not `comment`) to the model for which comment should be added (e.g. Post) and the appropriate imports as shown below:

```python
from django.contrib.contenttypes.fields import GenericRelation
from comment.models import Comment

class Post(models.Model):
	author = models.ForeignKey(User)
	title = models.CharField(max_length=200)
	body = models.TextField()
	# the field name should be comments
	comments = GenericRelation(Comment)
```

### Step 2
`get_comments` tag uses 2 positional and 3 optional args:
#1. The instance of the model. (positional)
#2. User. (positional)
#3. oauth. (optional - Default is false)
#4. profile_app_name. (optional)
#5. profile_model_name. (optional)


`include_static` this tag will include required jquery and javascript file.
`include_bootstrap` for bootstrap 4.1.1 if it's already included in your project, get rid of this tag.

In your template (e.g. post-detail.html) add the following template tags where object is the instance of post.

```python
{% load comment_tags %}  # Loading the template tag
{% get_comments object request.user %}  # Include all the comments belonging to a certain object
{% include_bootstrap %} # Include bootstrap 4.1.1
{% include_static %} # Include jQuery 3.2.1 and required js file
```
If you have profile model for the user and you would like to show the profile image on each comment you need to pass the profile_app_name and profile_model_name arguments to get_comments tag. (e.g if user profile app is called `accounts` and profile model is called `UserProfile`) the tag will look like the following:

```python
{% load comment_tags %}  # Loading the template tag
{% get_comments object request.user profile_app_name='accounts' profile_model_name='userprofile'%}  # Include all the comments belonging to a certain object
{% include_bootstrap %} # Include bootstrap 4.1.1
{% include_static %} # Include jQuery 3.2.1 and required js file
```

---


## Styling
If you want to customize your comments style do the following steps:
#. Create a comment.css file inside your static/css directory.
#. The new created file will overwrite the file used in the app.


and you're done.