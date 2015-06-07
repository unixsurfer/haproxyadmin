.. _haproxy:

HAProxy Operations
------------------

Get some information about the running processes

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
    'test.foo.com'
    >>>
    >>> hap.totalrequests
    796

.. note::
    This is the total number of requests that are processed by HAProxy.
    It counts requests for frontends and backends. Don't forget that
    a single client request passes HAProxy twice.

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


Get a list of :class:`Frontend <.Frontend>` objects for each available frontend

.. code:: python

    >>> frontends = hap.frontends()
    >>> for f in frontends:
    ...    print(f.name)
    ...
    frontend_proc1
    haproxy
    frontend1_proc34
    frontend2_proc34
    frontend_proc2


Get a :class:`Frontend <.Frontend>` object for a single frontend

.. code:: python

    >>> frontend1 = hap.frontend('frontend1_proc34')
    >>> frontend1.name, frontend1.process_nb
    ('frontend1_proc34', [4, 3])

Get a list of :class:`Backend <.Backend>` objects for each available backend

.. code:: python

    >>> backends = hap.backends()
    >>> for b in backends:
    ...    print(b.name)
    ...
    haproxy
    backend1_proc34
    backend_proc2
    backend_proc1
    backend2_proc34

Get a :class:`Backend <.Backend>` object for a single backend

.. code:: python

    >>> backend1 = hap.backend('backend1_proc34')
    >>> backend1.name, backend1.process_nb
    ('backend1_proc34', [4, 3])
