.. _haproxy:

HAProxy Operations
==================

Get some information about the running processes
------------------------------------------------

.. code:: python

    >>> hap.processids
    [871, 870, 869, 868]
    >>>
    >>> hap.description
    'Test server'
    >>>
    >>> hap.releasedate
    '2014/10/31'
    >>>
    >>> hap.version
    '1.5.8'
    >>>
    >>> hap.uptime
    '2d 0h55m09s'
    >>>
    >>> hap.uptimesec
    176112
    >>>
    >>> hap.nodename
    'axilleas'
    >>>
    >>> hap.totalrequests
    796

.. note::
    This is the total number of requests that are processed by HAProxy.
    It counts requests for frontends and backends. Don't forget that
    a single client request passes HAProxy twice.

Change global settings
----------------------

Dynamically change the specified global maxconn setting.

.. code:: python

    >>> print(hap.maxconn)
    40000
    >>> hap.setmaxconn(5000)
    True
    >>> print(hap.maxconn)
    20000
    >>>

.. note:: New setting is applied per process and the sum is returned.


