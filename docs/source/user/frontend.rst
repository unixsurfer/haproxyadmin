.. _frontend:

Frontend Operations
-------------------

A quick way to check if a certain frontend exists

.. code:: python

    >>> frontends = hap.frontends()
    >>> if 'frontend2_proc34' in frontends:
    ...    print('have it')
    ...
    have it
    >>> if 'frontend2_proc34foo' in frontends:
    ...    print('have it')
    ...
    >>>

Change maximum connections to all frontends

.. code:: python

    >>> frontends = hap.frontends()
    >>> for f in frontends:
    ...    print(f.maxconn, f.name)
    ...    f.setmaxconn(10000)
    ...    print(f.maxconn, f.name)
    ...    print('---------------')
    ...
    3000 haproxy-stats2
    True
    10000 haproxy-stats2
    ---------------
    6000 frontend1_proc34
    True
    20000 frontend1_proc34
    ---------------
    6000 frontend2_proc34
    True
    20000 frontend2_proc34
    ---------------
    3000 frontend_proc2
    True
    10000 frontend_proc2
    ---------------
    3000 haproxy-stats
    True
    10000 haproxy-stats
    ---------------
    3000 haproxy-stats3
    True
    10000 haproxy-stats3
    ---------------
    3000 haproxy-stats4
    True
    10000 haproxy-stats4
    ---------------
    3000 frontend_proc1
    True
    10000 frontend_proc1
    ---------------

Do the same only on specific frontend

.. code:: python

    >>> frontend = hap.frontend('frontend1_proc34')
    >>> frontend.maxconn
    20000
    >>> frontend.setmaxconn(50000)
    True
    >>> frontend.maxconn
    100000


Disable and enable a frontend

.. code:: python

    >>> frontend = hap.frontend('frontend1_proc34')
    >>> frontend.status
    'OPEN'
    >>> frontend.disable()
    True
    >>> frontend.status
    'STOP'
    >>> frontend.enable()
    True
    >>> frontend.status
    'OPEN'

Shutdown a frontend

.. code:: python

    >>> frontend.shutdown()
    True

.. warning::
    HAProxy removes from the running configuration the frontend, so
    further operations on the frontend will return an error.

.. code:: python

    >>> frontend.status
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "/..ages/haproxyadmin/frontend.py", line 243, in status
        'status')
    File "/...ages/haproxyadmin/utils.py", line 168, in cmd_across_all_procs
        (getattr(obj, 'process_nb'), getattr(obj, method)(*arg))
    File "/...ages/haproxyadmin/internal.py", line 210, in metric
        getattr(self.hap_process.frontends_stats()[self.name], name))
    KeyError: 'frontend1_proc34'


Retrieve various statistics

.. code:: python

    >>> frontend = hap.frontend('frontend2_proc34')
    >>> for m in FRONTEND_METRICS:
    ...    print("name {} value {}".format(m, frontend.metric(m)))
    ...
    name bin value 380
    name bout value 1065
    name comp_byp value 0
    name comp_in value 0
    name comp_out value 0
    name comp_rsp value 0
    name dreq value 0
    name dresp value 0
    name ereq value 0
    name hrsp_1xx value 0
    name hrsp_2xx value 0
    name hrsp_3xx value 0
    name hrsp_4xx value 0
    name hrsp_5xx value 5
    name hrsp_other value 0
    name rate value 0
    name rate_lim value 200000
    name rate_max value 2
    name req_rate value 0
    name req_rate_max value 2
    name req_tot value 5
    name scur value 0
    name slim value 20000
    name smax value 3
    name stot value 5
    >>>
    >>> frontend.process_nb
    [4, 3]
    >>> frontend.requests_per_process()
    [(4, 2), (3, 3)]
    >>> frontend.requests
    5
    >>>


.. note::
    ``requests`` returns HTTP requests that are processed by the frontend.
    If the frontend is in TCP mode the number will be always 0 and *stot*
    metric should be used to retrieve the number of TCP requests processsed.


Read :class:`Frontend <.Frontend>` class for more information.
