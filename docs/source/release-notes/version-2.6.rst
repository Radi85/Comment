=========================
Django-comments-dab v2.6
=========================

v2.6.0
-------

Features
^^^^^^^^^

- `#43`_ - Add thread (content-type and parent comment) subscription.
- `#43`_ - Send email notification to thread's subscribers on creating new comment.
- `#83`_ - Add ordering option for comments.
- `#117`_ - Add support for customization of user fields in the api.
- `#128`_ - Allow custom user model fields.
- `#142`_ - Extend ui customization.
- `#158`_ - Allow rendering new line in comment.

.. _#43: https://github.com/Radi85/Comment/issues/43
.. _#83: https://github.com/Radi85/Comment/issues/83
.. _#117: https://github.com/Radi85/Comment/issues/117
.. _#128: https://github.com/Radi85/Comment/issues/128
.. _#142: https://github.com/Radi85/Comment/issues/142
.. _#158: https://github.com/Radi85/Comment/issues/158

Bug fixes
^^^^^^^^^

- `#135`_ - Fix modal X button issue.
- `#139`_ - Fix url resolving issue.
- `#157`_ - Fix pluralization issue.

.. _#135: https://github.com/Radi85/Comment/issues/135
.. _#139: https://github.com/Radi85/Comment/issues/139
.. _#157: https://github.com/Radi85/Comment/issues/157

Codebase enhancement
^^^^^^^^^^^^^^^^^^^^^

- `#112`_ - Reduce testing time in pipeline.
- `#122`_ - Code clean up.
- `#129`_ - Update development guideline.
- `#132`_ and `#137`_ - Tests enhancement and refactoring.
- `#144`_ - Move common logic from views to mixin.
- `#150`_ - Unify django views responses.
- `#165`_ - Solve CI issue with django master.

.. _#112: https://github.com/Radi85/Comment/issues/112
.. _#122: https://github.com/Radi85/Comment/issues/43
.. _#129: https://github.com/Radi85/Comment/issues/43
.. _#132: https://github.com/Radi85/Comment/issues/132
.. _#137: https://github.com/Radi85/Comment/issues/137
.. _#144: https://github.com/Radi85/Comment/issues/144
.. _#150: https://github.com/Radi85/Comment/issues/150
.. _#165: https://github.com/Radi85/Comment/issues/165


v2.6.1
-------

Features
^^^^^^^^^

- `#163`_ - Add option for default profile pic location.

.. _#163: https://github.com/Radi85/Comment/issues/163

Bug fixes
^^^^^^^^^

- `#168`_ - Fix redirect path after login (Pass `request` object in template context).
- `#175`_ - Fix creating replies when subscription is disabled.

.. _#168: https://github.com/Radi85/Comment/issues/168
.. _#175: https://github.com/Radi85/Comment/issues/175

Codebase enhancement
^^^^^^^^^^^^^^^^^^^^^

- `#147`_ - Add missing step to setup documentation.
- `#173`_ - Rename default django branch to main.

.. _#147: https://github.com/Radi85/Comment/issues/147
.. _#173: https://github.com/Radi85/Comment/issues/173
