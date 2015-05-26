.. _api:

Developer Interface
===================

This part of the documentation covers all the available interfaces of
`haproxyadmin package`_. Public and internal interfaces are described.

:class:`HAProxy <.HAProxy>`, :class:`Frontend <.Frontend>`, :class:`Pool <.Pool>`
and :class:`PoolMember <.PoolMember>` classes are the main 4 public interfaces.
These classes provide methods to run various operations. `HAProxy`_ provides a
several statistics which can be retrieved by callin ``metric()``, see
`HAProxy statistics`_ for the full list of statistics.

:py:mod:`haproxyadmin.internal` module provides a set of classes that are not
meant for external use.


.. contents::

.. automodule:: haproxyadmin.haproxy

.. autoclass:: HAProxy
   :members:

.. automodule:: haproxyadmin.frontend


.. autoclass:: haproxyadmin.frontend.Frontend
   :members:

.. automodule:: haproxyadmin.pool

.. autoclass:: Pool
   :members:

.. automodule:: haproxyadmin.poolmember

.. autoclass:: PoolMember
   :members:

.. automodule:: haproxyadmin.internal
   :members:
   :private-members:

.. automodule:: haproxyadmin.utils
   :members:

.. automodule:: haproxyadmin.exceptions

.. autoclass:: CommandFailed

.. autoclass:: MultipleCommandResults

.. autoclass:: IncosistentData


Constants
---------

Metric names
^^^^^^^^^^^^

Various stats field names for which a value can be retrieved by using
``metric`` method available in all public and internal interfaces.

.. autodata:: haproxyadmin.haproxy.FRONTEND_METRICS

.. autodata:: haproxyadmin.haproxy.POOL_METRICS

.. autodata:: haproxyadmin.haproxy.SERVER_METRICS

Aggregation rules
^^^^^^^^^^^^^^^^^

The following 2 constants define the type of aggregation, either sum or
average, which is performed for values returned by all HAProxy processes.

.. autodata:: haproxyadmin.utils.METRICS_SUM

.. autodata:: haproxyadmin.utils.METRICS_AVG


Valid server states
^^^^^^^^^^^^^^^^^^^

A list of constants to use in ``setstate`` of :class:`.PoolMember` to change
the state of a server.

.. autodata:: haproxyadmin.haproxy.STATE_ENABLE

.. autodata:: haproxyadmin.haproxy.STATE_DISABLE

.. autodata:: haproxyadmin.haproxy.STATE_READY

.. autodata:: haproxyadmin.haproxy.STATE_DRAIN

.. autodata:: haproxyadmin.haproxy.STATE_MAINT


.. _HAProxy statistics: http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#9
.. _HAProxy: http://www.haproxy.org/
.. _haproxyadmin package: https://github.com/unixsurfer/haproxyadmin