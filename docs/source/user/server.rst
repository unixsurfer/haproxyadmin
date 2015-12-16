.. _server:

Server Operations
-----------------

A quick way to check if a certain server exists

.. code:: python

    >>> servers = hap.servers()
    >>> if 'bck_all_srv1' in servers:
    ...    print("have it")
    ...
    have it
    >>> if 'bck_all_srv1foo' in servers:
    ...    print("have it")
    ...
    >>>

Retrieve various statistics

.. code:: python

    >>> backend = hap.backend('backend1_proc34')
    >>> for server in backend.servers():
    ...    print(server.name)
    ...    for m in SERVER_METRICS:
    ...       print("name {} value {}".format(m, server.metric(m)))
    ...    print("-----------")
    ...
    bck1_proc34_srv2
    name qcur value 0
    name qmax value 0
    name scur value 0
    name smax value 0
    name stot value 0
    name bin value 0
    name bout value 0
    name dresp value 0
    name econ value 0
    name eresp value 0
    name wretr value 0
    name wredis value 0
    name weight value 1
    name act value 1
    name bck value 0
    name chkfail value 6
    name chkdown value 4
    name lastchg value 39464
    name downtime value 47702
    name qlimit value 0
    name throttle value 0
    name lbtot value 0
    name rate value 0
    name rate_max value 0
    name check_duration value 5001
    name hrsp_1xx value 0
    name hrsp_2xx value 0
    name hrsp_3xx value 0
    name hrsp_4xx value 0
    name hrsp_5xx value 0
    name hrsp_other value 0
    name cli_abrt value 0
    name srv_abrt value 0
    name lastsess value -1
    name qtime value 0
    name ctime value 0
    name rtime value 0
    name ttime value 0
    -----------
    bck1_proc34_srv1
    name qcur value 0
    name qmax value 0
    name scur value 0
    name smax value 0
    name stot value 0
    name bin value 0
    name bout value 0
    name dresp value 0
    name econ value 0
    name eresp value 0
    name wretr value 0
    name wredis value 0
    name weight value 1
    name act value 1
    name bck value 0
    name chkfail value 6
    name chkdown value 4
    name lastchg value 39464
    name downtime value 47702
    name qlimit value 0
    name throttle value 0
    name lbtot value 0
    name rate value 0
    name rate_max value 0
    name check_duration value 5001
    name hrsp_1xx value 0
    name hrsp_2xx value 0
    name hrsp_3xx value 0
    name hrsp_4xx value 0
    name hrsp_5xx value 0
    name hrsp_other value 0
    name cli_abrt value 0
    name srv_abrt value 0
    name lastsess value -1
    name qtime value 0
    name ctime value 0
    name rtime value 0
    name ttime value 0
    -----------
    bck_all_srv1
    name qcur value 0
    name qmax value 0
    name scur value 0
    name smax value 0
    name stot value 0
    name bin value 0
    name bout value 0
    name dresp value 0
    name econ value 0
    name eresp value 0
    name wretr value 0
    name wredis value 0
    name weight value 1
    name act value 1
    name bck value 0
    name chkfail value 6
    name chkdown value 4
    name lastchg value 39462
    name downtime value 47700
    name qlimit value 0
    name throttle value 0
    name lbtot value 0
    name rate value 0
    name rate_max value 0
    name check_duration value 5001
    name hrsp_1xx value 0
    name hrsp_2xx value 0
    name hrsp_3xx value 0
    name hrsp_4xx value 0
    name hrsp_5xx value 0
    name hrsp_other value 0
    name cli_abrt value 0
    name srv_abrt value 0
    name lastsess value -1
    name qtime value 0
    name ctime value 0
    name rtime value 0
    name ttime value 0
    -----------
    >>>

Change weight of server in a backend

.. code:: python

    >>> backend = hap.backend('backend1_proc34')
    >>> server = backend.server('bck_all_srv1')
    >>> server.weight
    100
    >>> server.setweight('20%')
    True
    >>> server.weight
    20
    >>> server.setweight(58)
    True
    >>> server.weight
    58

.. note::
    If the value ends with the '%' sign, then the new weight will be relative
    to the initially configured weight. Absolute weights are permitted between
    0 and 256.

or across all backends

.. code:: python

    >>> server_per_backend = hap.server('bck_all_srv1')
    >>> for server in server_per_backend:
    ...    print(server.backendname, server.weight)
    ...    server.setweight(8)
    ...    print(server.backendname, server.weight)
    ...
    backend2_proc34 1
    True
    backend2_proc34 8
    backend1_proc34 0
    True
    backend1_proc34 8
    backend_proc1 100
    True
    backend_proc1 8
    >>>

Terminate all the sessions attached to the specified server.

.. code:: python

    >>> backend = hap.backend('backend1_proc34')
    >>> server = backend.server('bck_all_srv1')
    >>> server.metric('scur')
    8
    >>> server.shutdown()
    True
    >>> server.metric('scur')
    0

Disable a server in a backend

.. code:: python

    >>> server = hap.server('member_bkall', backend='backend_proc1')[0]
    >>> server.setstate(haproxy.STATE_DISABLE)
    True
    >>> server.status
    'MAINT'
    >>> server.setstate(haproxy.STATE_ENABLE)
    True
    >>> server.status
    'no check'

Get status of server

.. code:: python

    >>> backend = hap.backend('backend1_proc34')
    >>> server = backend.server('bck_all_srv1')
    >>> server.last_agent_check
    ''
    >>> server.check_status
    'L4TOUT'
    >>> server.check_
    server.check_code    server.check_status
    >>> server.check_code
    ''
    >>> server.status
    'DOWN'
    >>>

Read :class:`Server <.Server>` class for more information.
