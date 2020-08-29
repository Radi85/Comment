Example
========

Using local virtual env

.. code:: bash

    $ git clone https://github.com/Radi85/Comment.git  # or clone your forked repo
    $ cd Comment
    $ python3 -m venv local_env  # or any name. local_env is in .gitignore
    $ export DEBUG=True
    $ source local_env/bin/activate
    $ pip install -r test/example/requirements.txt
    $ python manage.py migrate
    $ python manage.py create_initial_data
    $ python manage.py runserver


Or run with docker

.. code:: bash

    $ git clone https://github.com/Radi85/Comment.git  # or clone your forked repo
    $ cd Comment
    $ docker-compose up


Login with:

    username: ``test``

    password: ``test``

.. image:: ../_static/img/comment.gif
