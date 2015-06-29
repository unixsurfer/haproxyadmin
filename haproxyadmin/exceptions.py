# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
haproxyadmin.exceptions
~~~~~~~~~~~~~~~~~~~~~~~

This module contains the set of haproxyadmin' exceptions.

"""


class CommandFailed(Exception):
    """Raised when a command to HAProxy returned an error.

    :param message: error message.
    :type message: ``string``
    """
    def __init__(self, message):
        super(CommandFailed, self).__init__(message)


class MultipleCommandResults(Exception):
    """Command returned different results per HAProxy process."""
    def __init__(self, results):
        self.message = 'Received different result per HAProxy process'
        self.results = results
        super(MultipleCommandResults, self).__init__(self.message)


class IncosistentData(Exception):
    """Data across all processes is not the same."""
    def __init__(self, results):
        self.message = 'Received different data per HAProxy process'
        self.results = results
        super(IncosistentData, self).__init__(self.message)


class SocketPermissionError(Exception):
    """Raised when permissions are not granted to access socket file.

    :param socket_file: socket file.
    :type socket_file: ``string``
    """
    def __init__(self, socket_file):
        self.message = 'No permissions are granted to access socket file'
        self.socket_file = socket_file
        super(SocketPermissionError, self).__init__(self.message)


class SocketConnectionError(Exception):
    """Raised when socket file is not bound to a process.

    :param socket_file: socket file.
    :type socket_file: ``string``
    """
    def __init__(self, socket_file):
        self.message = 'No process is bound to socket file'
        self.socket_file = socket_file
        super(SocketConnectionError, self).__init__(self.message)


class SocketApplicationError(Exception):
    """Raised when we connect to a socket and find HAProxy is not bound to it.

    :param socket_file: socket file.
    :type socket_file: ``string``
    """
    def __init__(self, socket_file):
        self.message = 'HAProxy is not bound to socket file'
        self.socket_file = socket_file
        super(SocketApplicationError, self).__init__(self.message)


class SocketTransportError(Exception):
    """Raised when endpoint of socket hasn't closed an old connection.

    .. note::
       It only occurs in cases where HAProxy is ~90% CPU utilization for
       processing traffic and we reconnect to the socket too
       fast and as a result HAProxy doesn't have enough time to close the
       previous connection.

    :param message: error message.
    :type message: ``string``
    """
    def __init__(self, message):
        super(SocketTransportError, self).__init__(message)


class SocketTimeout(Exception):
    """Raised when we timeout on the socket.

    :param message: error message.
    :type message: ``string``
    """
    def __init__(self, message):
        super(SocketTimeout, self).__init__(message)
