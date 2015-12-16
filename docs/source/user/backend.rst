.. _backend:

Backend Operations
------------------

A quick way to check if a certain backend exists

.. code:: python

    >>> backends = hap.backends()
    >>> if 'backend1_proc34' in backends:
    ...    print('have it')
    ...
    have it
    >>> if 'backend1_proc34foo' in backends:
    ...    print('have it')
    ...
    >>>

Retrieve various statistics

.. code:: python

    >>> backend = hap.backend('backend1_proc34')
    >>> for m in BACKEND_METRICS:
    ...     print("name {} value {}".format(m, backend.metric(m)))
    ...
    name act value 3
    name bck value 0
    name bin value 0
    name bout value 0
    name chkdown value 2
    name cli_abrt value 0
    name comp_byp value 0
    name comp_in value 0
    name comp_out value 0
    name comp_rsp value 0
    name ctime value 0
    name downtime value 8237
    name dreq value 0
    name dresp value 0
    name econ value 0
    name eresp value 0
    name hrsp_1xx value 0
    name hrsp_2xx value 0
    name hrsp_3xx value 0
    name hrsp_4xx value 0
    name hrsp_5xx value 0
    name hrsp_other value 0
    name lastchg value 11373
    name lastsess value -1
    name lbtot value 0
    name qcur value 0
    name qmax value 0
    name qtime value 0
    name rate value 0
    name rate_max value 0
    name rtime value 0
    name scur value 0
    name slim value 200000
    name smax value 0
    name srv_abrt value 0
    name stot value 0
    name ttime value 0
    name weight value 3
    name wredis value 0
    name wretr value 0
    >>>
    >>>
    >>> backend.process_nb
    [4, 3]
    >>> backend.requests_per_process()
    [(4, 2), (3, 3)]
    >>> backend.requests
    5
    >>>

Get all servers in across all backends

.. code:: python

    >>> for backend in backends:
    >>> backends = hap.backends()
    ...    print(backend.name, backend.requests, backend.process_nb)
    ...    servers = backend.servers()
    ...    for server in servers:
    ...       print(" ", server.name, server.requests)
    ...
    backend_proc2 100 [2]
      bck_proc2_srv4_proc2 25
      bck_proc2_srv3_proc2 25
      bck_proc2_srv1_proc2 25
      bck_proc2_srv2_proc2 25
    haproxy 0 [4, 3, 2, 1]
    backend1_proc34 16 [4, 3]
      bck1_proc34_srv1 6
      bck_all_srv1 5
      bck1_proc34_srv2 5
    backend_proc1 29 [1]
      member2_proc1 14
      member1_proc1 15
      bck_all_srv1 0
    backend2_proc34 100 [4, 3]
      bck2_proc34_srv2 97
      bck2_proc34_srv1 2
      bck_all_srv1 1
    >>>

Get servers of a specific backend

.. code:: python

    >>> backend = hap.backend('backend1_proc34')
    >>> for s in backend.servers():
    ...    print(s.name, s.status, s.weight)
    ...
    bck1_proc34_srv2 UP 1
    bck_all_srv1 UP 1
    bck1_proc34_srv1 UP 1
    >>>

Get a specific server from a backend

.. code:: python

    >>> s1 = backend.server('bck1_proc34_srv2')
    >>> s1.name, s1.backendname, s1.status, s1.requests, s1.weight
    ('bck1_proc34_srv2', 'backend1_proc34', 'UP', 9, 1)

Read :class:`Backend <.Backend>` class for more information.
