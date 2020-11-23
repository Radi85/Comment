Contributing
=============

Django Comments Dab is developed and maintained by developers in an Open Source manner.
Any support is welcome. You could help by writing documentation, pull-requests, report issues and/or translations.

Development
^^^^^^^^^^^

To start development on this project, fork_ this repository and follow the guidelines given below.

.. _fork: https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo

.. code:: bash

    # clone the forked repository
    $ git clone YOUR_FORKED_REPO_URL

    # create a virtual environment
    $ python3 -m venv local_env
    # activate the virtual environment
    $ source local_env/bin/activate
    # install dependencies
    (venv) $ pip install -e . -r example/requirements.txt

    (venv) $ export DEBUG="True"
    # migrate the changes to database
    (venv) $ python manage.py migrate
    # prepare initial data
    (venv) $ python manage.py create_initial_data
    # start the development server
    (venv) $ python manage.py runserver

Or run with docker

.. code:: bash

    $ git clone YOUR_FORKED_REPO_URL
    $ cd Comment
    $ docker-compose up


Login with:

    username: ``test``

    password: ``test``

Testing
^^^^^^^

To run tests against a particular ``python`` and ``django`` version installed inside your virtual environment, you may use:

.. code:: bash

    (venv) $ python manage.py test


To run tests against all supported ``python`` and ``django`` versions, you may run:

.. code:: bash

    # install dependency
    (venv) $ pip install tox
    # run tests
    (venv) $ tox


Translations
^^^^^^^^^^^^

To add translations in your native language, please take a look at the :ref:`instuctions for translators<Adding Support for Translation>`.
