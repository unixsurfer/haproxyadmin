.. _api:

Developer Interface
===================

This part of the documentation covers all the available interfaces of
`haproxyadmin package`_. Public and internal interfaces are described.

:class:`HAProxy <.HAProxy>`, :class:`Frontend <.Frontend>`, :class:`Backend <.Backend>`
and :class:`server <.Server>` classes are the main 4 public interfaces.
These classes provide methods to run various operations. `HAProxy`_ provides a
several statistics which can be retrieved by calling ``metric()``, see
`HAProxy statistics`_ for the full list of statistics.

:py:mod:`haproxyadmin.internal` module provides a set of classes that are not
meant for external use.


.. toctree::
   :maxdepth: 2

.. automodule:: haproxyadmin.haproxy

.. autoclass:: HAProxy
   :members:

.. automodule:: haproxyadmin.frontend


.. autoclass:: haproxyadmin.frontend.Frontend
   :members:

.. automodule:: haproxyadmin.backend

.. autoclass:: Backend
   :members:

.. automodule:: haproxyadmin.server

.. autoclass:: Server
   :members:

.. automodule:: haproxyadmin.internal.haproxy
   :members:
   :private-members:

.. automodule:: haproxyadmin.internal.frontend
   :members:
   :private-members:

.. automodule:: haproxyadmin.internal.backend
   :members:
   :private-members:

.. automodule:: haproxyadmin.internal.server
   :members:
   :private-members:

.. automodule:: haproxyadmin.utils
   :members:

.. automodule:: haproxyadmin.exceptions
   :members:


Constants
---------

Metric names
^^^^^^^^^^^^

Various stats field names for which a value can be retrieved by using
``metric`` method available in all public and internal interfaces.

.. data:: haproxyadmin.FRONTEND_METRICS
   :annotation: = a list of metric names for retrieving varius statistics for
     frontends

.. data:: haproxyadmin.BACKEND_METRICS
   :annotation: = a list of metric names for retrieving varius statistics for
     backends

.. data:: haproxyadmin.SERVER_METRICS
   :annotation: = a list of metric names for retrieving varius statistics for
     servers

Aggregation rules
^^^^^^^^^^^^^^^^^

The following 2 constants define the type of aggregation, either sum or
average, which is performed for values returned by all HAProxy processes.

.. autodata:: haproxyadmin.utils.METRICS_SUM

.. autodata:: haproxyadmin.utils.METRICS_AVG


Valid server states
^^^^^^^^^^^^^^^^^^^

A list of constants to use in ``setstate`` of :class:`.Server` to change
the state of a server.

.. autodata:: haproxyadmin.haproxy.STATE_ENABLE

.. autodata:: haproxyadmin.haproxy.STATE_DISABLE

.. autodata:: haproxyadmin.haproxy.STATE_READY

.. autodata:: haproxyadmin.haproxy.STATE_DRAIN

.. autodata:: haproxyadmin.haproxy.STATE_MAINT


.. _HAProxy statistics: http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#9
.. _HAProxy: http://www.haproxy.org/
.. _haproxyadmin package: https://github.com/unixsurfer/haproxyadmin
