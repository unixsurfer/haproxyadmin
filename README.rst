.. haproxyadmin
.. README.rst

============
haproxyadmin
============

    *A Python library to manage HAProxy via stats socket.*

.. contents::


Introduction
------------

**haproxyadmin** is a Python library for interacting with `HAProxy`_
load balancer to perform operations such as enabling/disabling servers.
It does that by issuing the appropriate commands over the `stats socket`_
provided by HAProxy. It also uses that stats socket for retrieving
statistics and changing settings.

HAProxy is a multi-process daemon and each process can only be accessed by a
distinct stats socket. There isn't any shared memory for all these processes.
That means that if a frontend or backend is managed by more than one processes,
you have to find which stats socket you need to send the query/command.
This makes the life of a sysadmin a bit difficult as he has to keep track of
which stats socket to use for a given object(frontend/backend/server).

**haproxyadmin** resolves this problem by presenting objects as single entities
even when they are managed by multiple processes. It also supports aggregation
for various statistics provided by HAProxy. For instance, to report the
requests processed by a frontend it queries all processes which manage that
frontend and return the sum.

The library works with Python 2.7 and Python 3.6, but for development and
testing Python 3.6 is used. The `Six Python 2 and 3 Compatibility Library`_
is being used to provide the necessary wrapping over the differences between
these 2 major versions of Python.


.. code-block:: python


    >>> from haproxyadmin import haproxy
    >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
    >>> frontends = hap.frontends()
    >>> for frontend in frontends:
    ...     print(frontend.name, frontend.requests, frontend.process_nb)
    ...
    frontend_proc2 0 [2]
    haproxy 0 [4, 3, 2, 1]
    frontend_proc1 0 [1]
    frontend1_proc34 0 [4, 3]
    frontend2_proc34 0 [4, 3]
    >>>
    >>>
    >>> backends = hap.backends()
    >>> for backend in backends:
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


The documentation of the library is available at http://haproxyadmin.readthedocs.org


Features
--------

- HAProxy in multi-process mode (nbproc >1)
- UNIX stats socket, no support for querying HTTP statistics page
- Frontend operations
- Backend operations
- Server operations
- ACL operations
- MAP operations
- Aggregation on various statistics
- Change global options for HAProxy


Installation
------------

Use pip::

    pip install haproxyadmin

From Source::

   sudo python setup.py install

Build (source) RPMs::

   python setup.py clean --all; python setup.py bdist_rpm

Build a source archive for manual installation::

   python setup.py sdist

Release
-------

#. Bump versions in docs/source/conf.py and haproxyadmin/__init__.py

#. Commit above change with::

      git commit -av -m'RELEASE 0.1.3 version'

#. Create a signed tag, pbr will use this for the version number::

      git tag -s 0.1.3 -m 'bump release'

#. Create the source distribution archive (the archive will be placed in the **dist** directory)::

      python setup.py sdist

#. pbr will update ChangeLog file and we want to squeeze them to the previous commit thus we run::

      git commit -av --amend

#. Move current tag to the last commit::

      git tag -fs 0.1.3 -m 'bump release'

#. Push changes::

      git push;git push --tags


Development
-----------
I would love to hear what other people think about **haproxyadmin** and provide
feedback. Please post your comments, bug reports, wishes on my `issues page
<https://github.com/unixsurfer/haproxyadmin/issues>`_.

Licensing
---------

Apache 2.0


Acknowledgement
---------------
This program was originally developed for Booking.com.  With approval
from Booking.com, the code was generalised and published as Open Source
on github, for which the author would like to express his gratitude.

Contacts
--------

**Project website**: https://github.com/unixsurfer/haproxyadmin

**Author**: Pavlos Parissis <pavlos.parissis@gmail.com>

.. _HAProxy: http://www.haproxy.org/
.. _stats socket: http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#9.2
.. _Six Python 2 and 3 Compatibility Library: https://pythonhosted.org/six/

