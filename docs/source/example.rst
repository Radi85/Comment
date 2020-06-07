Example
=======

.. code:: bash

    $ git clone https://github.com/Radi85/Comment.git  # or clone your forked repo
    $ cd Comment
    $ python3 -m virtualenv local_env  # or any name. local_env is in .gitignore
    $ source local_env/bin/activate
    $ pip install -r test/example/requirements.txt
    $ python test/example/manage.py runserver


Login with:

    username: ``test``

    password: ``django-comments``

.. image:: ../_static/img/comment.gif
