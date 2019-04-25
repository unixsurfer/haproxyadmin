# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
haproxyadmin.exceptions
~~~~~~~~~~~~~~~~~~~~~~~

This module contains the set of haproxyadmin' exceptions with the following
hierarchy::

    HAProxyBaseError
    ├── CommandFailed
    ├── HAProxyDataError
    │   ├── IncosistentData
    │   └── MultipleCommandResults
    └── HAProxySocketError
        ├── SocketApplicationError
        ├── SocketConnectionError
        ├── SocketPermissionError
        ├── SocketTimeout
        └── SocketTransportError
"""


class HAProxyBaseError(Exception):
    """haproxyadmin base exception.

    :param message: error message.
    :type message: ``string``
    """

    message = ''

    def __init__(self, message=''):
        if message:
            self.message = message
        super(HAProxyBaseError, self).__init__(self.message)


class CommandFailed(HAProxyBaseError):
    """Raised when a command to HAProxy returned an error."""


class HAProxyDataError(HAProxyBaseError):
    """Base DataError class.

    :param results: A structure which contains data returned be each socket.
    :type results: ``list`` of ``list``
    """

    def __init__(self, results):
        self.results = results
        super(HAProxyDataError, self).__init__()


class MultipleCommandResults(HAProxyDataError):
    """Command returned different results per HAProxy process."""

    message = 'Received different result per HAProxy process'


class IncosistentData(HAProxyDataError):
    """Data across all processes is not the same."""

    message = 'Received different data per HAProxy process'


class HAProxySocketErrors(HAProxyBaseError):
    """Raised when at least one connection fails."""
    message = "Socket errors"
    def __init__(self, details):
        self.details = details
        super(HAProxySocketErrors, self).__init__()

class AllServersFailed(HAProxySocketErrors):
    message = "Failed to connected to all HAProxy servers"


class HAProxySocketError(HAProxyBaseError):
    """Base SocketError class.

    :param socket_file: socket file.
    :type socket_file: ``string``
    """

    def __init__(self, message, haproxy_server):
        self.haproxy_server = haproxy_server
        self.message = "{}: {!s}".format(message, self.haproxy_server)
        super(HAProxySocketError, self).__init__(self.message)


class SocketTimeout(HAProxySocketError):
    """Raised when we timeout on the socket."""

    message = 'Socket timed out'


class SocketPermissionError(HAProxySocketError):
    """Raised when permissions are not granted to access socket file."""

    message = 'No permissions are granted to access socket file'


class SocketConnectionError(HAProxySocketError):
    """Raised when socket file is not bound to a process."""

    message = 'No HAProxy process is bound to socket'


class SocketApplicationError(HAProxyBaseError):
    """Raised when we connect to a socket and HAProxy is not bound to it."""

    def __init__(self, haproxy_server):
        self.haproxy_server = haproxy_server
        self.message = "Process listening on {!s} isn't HAProxy!".format(
            self.haproxy_server)
        super(SocketApplicationError, self).__init__(self.message)

class SocketTransportError(HAProxySocketError):
    """Raised when endpoint of socket hasn't closed an old connection.

    .. note::
       It only occurs in cases where HAProxy is ~90% CPU utilization for
       processing traffic and we reconnect to the socket too
       fast and as a result HAProxy doesn't have enough time to close the
       previous connection.

    """

    message = 'Transport endpoint is already connected'
