# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
haproxyadmin.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of haproxyadmin' exceptions.

"""


class CommandFailed(Exception):
    """Raised when a command to HAProxy returned an error.

    Arguments:
        message (str): String returned by HAProxy
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
