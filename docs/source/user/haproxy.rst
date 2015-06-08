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
    ``totalrequests`` returns the total number of requests that are processed
    by HAProxy. It counts requests for frontends and backends. Don't forget that
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


Get a list of :class:`Frontend <.Frontend>` objects for all frontends

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

Get a list of :class:`Backend <.Backend>` objects for all backends

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

Get a list of :class:`Server <.Server>` objects for each server

.. code:: python

    >>> servers = hap.servers()
    >>> for s in servers:
    ...    print(s.name, s.backendname)
    ...
    bck1_proc34_srv1 backend1_proc34
    bck1_proc34_srv2 backend1_proc34
    bck_all_srv1 backend1_proc34
    bck_proc2_srv3_proc2 backend_proc2
    bck_proc2_srv1_proc2 backend_proc2
    bck_proc2_srv4_proc2 backend_proc2
    bck_proc2_srv2_proc2 backend_proc2
    member1_proc1 backend_proc1
    bck_all_srv1 backend_proc1
    member2_proc1 backend_proc1
    bck2_proc34_srv1 backend2_proc34
    bck_all_srv1 backend2_proc34
    bck2_proc34_srv2 backend2_proc34

.. note::
     if a server is member of more than 1 backends then muliple
     :class:`Server <.Server>` objects for the server is returned

Limit the list of server for a specific pool

.. code:: python

    >>> servers = hap.servers(backend='backend1_proc34')
    >>> for s in servers:
    ...    print(s.name, s.backendname)
    ...
    bck1_proc34_srv1 backend1_proc34
    bck1_proc34_srv2 backend1_proc34
    bck_all_srv1 backend1_proc34

Work on specific server across all backends

.. code:: python

    >>> s1 = hap.server(hostname='bck_all_srv1')
    >>> for x in s1:
    ...    print(x.name, x.backendname, x.status)
    ...    x.setstate(haproxy.STATE_DISABLE)
    ...    print(x.status)
    ...
    bck_all_srv1 backend1_proc34 DOWN
    True
    MAINT
    bck_all_srv1 backend_proc1 DOWN
    True
    MAINT
    bck_all_srv1 backend2_proc34 no check
    True
    MAINT


Examples for ACLs

.. code:: python

    >>> from pprint import pprint
    >>> pprint(hap.show_acl())
    ['# id (file) description',
    "0 (/etc/haproxy/wl_stats) pattern loaded from file '/etc/haproxy/wl_stats' "
    "used by acl at file '/etc/haproxy/haproxy.cfg' line 53",
    "1 () acl 'src' file '/etc/haproxy/haproxy.cfg' line 53",
    "3 () acl 'ssl_fc' file '/etc/haproxy/haproxy.cfg' line 85",
    '4 (/etc/haproxy/bl_frontend) pattern loaded from file '
    "'/etc/haproxy/bl_frontend' used by acl at file '/etc/haproxy/haproxy.cfg' "
    'line 97',
    "5 () acl 'src' file '/etc/haproxy/haproxy.cfg' line 97",
    "6 () acl 'path_beg' file '/etc/haproxy/haproxy.cfg' line 99",
    "7 () acl 'req.cook' file '/etc/haproxy/haproxy.cfg' line 114",
    "8 () acl 'req.cook' file '/etc/haproxy/haproxy.cfg' line 115",
    "9 () acl 'req.cook' file '/etc/haproxy/haproxy.cfg' line 116",
    '']
    >>> hap.show_acl(6)
    ['0x12ea940 /static/css/', '']
    >>> hap.add_acl(6, '/foobar')
    True
    >>> hap.show_acl(6)
    ['0x12ea940 /static/css/', '0x13a38b0 /foobar', '']
    >>> hap.add_acl(6, '/foobar')
    True
    >>> hap.show_acl(6)
    ['0x12ea940 /static/css/', '0x13a38b0 /foobar', '0x13a3930 /foobar', '']
    >>> hap.del_acl(6, '/foobar')
    True
    >>> hap.show_acl(6)
    ['0x12ea8a0 /static/js/', '0x12ea940 /static/css/', '']


Examples for MAPs

.. code:: python

    >>> from haproxyadmin import haproxy
    >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
    >>> hap.show_map(map=6)
    ['# id (file) description',
    "0 (/etc/haproxy/v-m1-bk) pattern loaded ...... line 82",
    '']
    >>> hap.show_map(0)
    ['0x1a78ab0 0 www.foo.com-0', '0x1a78b20 1 www.foo.com-1', '']


Manage MAPs

.. code:: python

    >>> hap.show_map(0)
    ['0x1a78b20 1 www.foo.com-1', '']
    >>> hap.add_map(0, '9', 'foo')
    True
    >>> hap.show_map(0)
    ['0x1a78b20 1 www.foo.com-1', '0x1b15c80 9 foo', '']

.. code:: python

    >>> hap.show_map(0)
    ['0x1b15cd0 9 foo', '0x1a78980 11 bar', '']
    >>> hap.del_map(0, '0x1b15cd0')
    True
    >>> hap.show_map(0)
    ['0x1a78980 11 bar', '']
    >>> hap.add_map(0, '22', 'bar22')
    True
    >>> hap.show_map(0)
    ['0x1a78980 11 bar', '0x1b15c00 22 bar22', '']
    >>> hap.del_map(0, '22')
    True
    >>> hap.show_map(0)
    ['0x1a78980 11 bar', '']

