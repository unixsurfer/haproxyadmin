.. haproxyadmin
.. README.rst

============
haproxyadmin
============

    *A Python library to manage HAProxy via stats socket.*

.. contents::


Introduction
------------

**haproxyadmin** is a Python library for interacting with `HAProxy
<http://www.haproxy.org>`_ load balancer to perform operations such as
enabling/disabling servers. It does that by issuing the appropriate commands
over the `stats socket <http://cbonte.github.io/haproxy-dconv/configuration-1.5.html#9.2>`_
provided by HAProxy.

HAProxy is a multi-process daemon and each process can be accessed by a
distinct stats socket. This makes the life of a Sysadmin a bit difficult
when he has to issue commands over these multiple sockets for performing
various operation tasks. **haproxyadmin** resolves this problem by presenting
objects such as frontends/pools/servers as single entities even when they are
managed by multiple processes.

The library works with Python 2.7 and Python 3.4, but for development and testing Python 3.4 is used. The `Six: Python 2 and 3 Compatibility Library <https://pythonhosted.org/six/>`_ is being used to provide the necessary wrapping over the differences between these 2 major versions of Python.

Examples
--------


API
---

Exceptions
~~~~~~~~~~


Installation
------------

From Source::

   sudo python setup.py install

Build (source) RPMs::

   python setup.py clean --all; python setup.py bdist_rpm

Booking.com instructions::

   python setup.py clean --all
   python setup.py sdist

Build a source archive for manual installation::

   python setup.py sdist


Release
-------

To make a release you should first create a signed tag, pbr will use this for the version number::

   git tag -s 0.0.9 -m 'bump release'
   git push --tags

Create the source distribution archive (the archive will be placed in the **dist** directory)::

   python setup.py sdist


Development
-----------
I would love to hear what other people think about **haproxyadmin** and provide
feedback. Please post your comments, bug reports, wishes on my `issues page
<https://github.com/unixsurfer/haproxyadmin/issues>`_.

Licensing
~~~~~~~~~

Apache 2.0


Acknowledgement
---------------
This program was originally developed for Booking.com.  With approval
from Booking.com, the code was generalised and published as Open Source
on github, for which the author would like to express his gratitude.

Contacts
--------

**Project website**: https://github.com/unixsurfer/haproxyadmin

**Author**: Palvos Parissis <pavlos.parissis@gmail.com>
