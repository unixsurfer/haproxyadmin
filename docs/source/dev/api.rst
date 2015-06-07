.. _api:

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

.. autodata:: haproxyadmin.haproxy.BACKEND_METRICS

.. autodata:: haproxyadmin.haproxy.SERVER_METRICS

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
