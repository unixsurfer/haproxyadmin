=======================================
Welcome to haproxyadmin's documentation
=======================================

.. toctree::
   :maxdepth: 2

   README_link.rst

User Guide
==========

This part of the documentation covers step-by-step instructions for getting
the most out of **haproxyadmin**. It begins by introducing operations related
to HAProxy process and then focus on providing the most frequent operations
for frontends, backends and servers. In all examples HAProxy is configured
with 4 processes, see example `HAProxy configuration`_.

In the code mentioned in the following sections the ``hap`` object has to be
created first.

.. code:: python

    >>> from haproxyadmin import haproxy
    >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
    >>>

.. warning:: Make sure you have appropriate privillage to write in the socket files.


.. toctree::
   :maxdepth: 2

   user/haproxy
   user/frontend
   user/backend
   user/server

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

   dev/api
   changelog
   TODO.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _HAProxy statistics: http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#9
.. _HAProxy: http://www.haproxy.org/
.. _haproxyadmin package: https://github.com/unixsurfer/haproxyadmin
.. _HAProxy configuration: https://raw.githubusercontent.com/unixsurfer/haproxyadmin/master/tools/haproxy.cfg
