=========================
Django-comments-dab v2.7
=========================

v2.7.0
-------

Features
^^^^^^^^^

- `#143`_ - Allow blocking users and emails.
- `#156`_ - Improve UI for commenting anonymously.
- `#203`_ - Enhance API docs by adding openapi and swagger page to RTD.
- `#215`_ - Reduce number of queries by prefetching foreign key objects on comment.
- `#218`_ - Add support for django ``3.2``.

.. _#143: https://github.com/Radi85/Comment/issues/143
.. _#156: https://github.com/Radi85/Comment/issues/156
.. _#203: https://github.com/Radi85/Comment/issues/203
.. _#215: https://github.com/Radi85/Comment/pull/215
.. _#218: https://github.com/Radi85/Comment/issues/218

Bug fixes
^^^^^^^^^

- `#202`_ - Fix response for state change on unflagged comments.
- `#210`_ - Reduce chances of XSS injections.
- `#213`_ - Fix namespace pollution caused by star imports.
- `#216`_ - Give warnings when deprecated template tag include_static is used.

.. _#202: https://github.com/Radi85/Comment/pull/202
.. _#210: https://github.com/Radi85/Comment/issues/210
.. _#213: https://github.com/Radi85/Comment/pull/213
.. _#216: https://github.com/Radi85/Comment/issues/216

Codebase enhancement
^^^^^^^^^^^^^^^^^^^^^

- `#205`_ - Enhance Coverage - Add tests for permissions.
- `#206`_ - Move metadata from setup.py to setup.cfg.
- `#200`_ and `#209`_ - Tests enhancement and refactoring.
- `#223`_ - Migrate to github actions for CI.
- `#225`_ - Run tests for all supported python and django versions.

.. _#205: https://github.com/Radi85/Comment/pull/205
.. _#206: https://github.com/Radi85/Comment/issues/206
.. _#200: https://github.com/Radi85/Comment/pull/200
.. _#209: https://github.com/Radi85/Comment/pull/209
.. _#223: https://github.com/Radi85/Comment/issues/223
.. _#225: https://github.com/Radi85/Comment/issues/225


v2.7.1
-------

Bug fixes
^^^^^^^^^

- `#230`_ - Fix closing of anonymous create comment modal.

.. _#230: https://github.com/Radi85/Comment/issues/230
