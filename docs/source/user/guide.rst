.. _guide:

User Guide
==========

This part of the documentation covers step-by-step instructions for getting
the most out of **haproxyadmin**. It begins by introducing operations related
to HAProxy process and then focus on providing the most frequent operations
for frontends, backends and servers. In all examples HAProxy is configured
with 4 processes, see example `HAProxy configuration`_.

A :class:`HAProxy <.HAProxy>` object with the name ``hap`` needs to be created
prior running the code mentioned in the following sections:

.. code:: python

    >>> from haproxyadmin import haproxy
    >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')

.. warning:: Make sure you have appropriate privillage to write in the socket files.


.. toctree::
   :maxdepth: 2

   haproxy
   frontend
   backend
   server


.. _HAProxy configuration: https://raw.githubusercontent.com/unixsurfer/haproxyadmin/master/tools/haproxy.cfg
