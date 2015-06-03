# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.internal
~~~~~~~~~~~~~~~~~~~~~

This module provides classes that are used within haproxyadmin for creating
objects to work with frontend, pool and pool server which associated with
with a single HAProxy process.

"""

import six
import socket
import time

from .utils import (info2dict, converter, stat2dict)


class _HAProxyProcess(object):
    """An object to a single HAProxy process.

    It acts as a communication pipe between the caller and individual
    HAProxy process using UNIX stats socket.

    :param socket_file: Full path of socket file.
    :type socket_file: string
    :param retry: (optional) Number of connect retries (defaults to 3)
    :type retry: integer
    :param retry_interval: (optional) Interval time in seconds between retries
                           (defaults to 2)
    :type retry_interval: integer
    """
    SUCCESS_OUTPUT_STRINGS = ['Done.', '']

    def __init__(self, socket_file, retry=3, retry_interval=2):
        self.socket_file = socket_file
        self.timer = time.time()
        self.hap_stats = {}
        self.hap_info = {}
        self.retry = retry
        self.retry_interval = retry_interval
        # process number associated with this object
        self.process_nb = self.proc_info()['Process_num']

    def send_command(self, command):
        """Send a command to HAProxy over UNIX stats socket.

        :param command: A valid command to execute
        :type command: string
        :return: Output. Newline character is stripped off.
        :rtype: list
        """
        unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # I haven't seen a case where a running process which holds a UNIX
        # socket will take more than few nanoseconds to accept a connection.
        # Thus I hard-code a timeout of 0.1ms
        unix_socket.settimeout(0.1)

        for attempt in range(1, self.retry + 1):
            try:
                unix_socket.connect(self.socket_file)
                unix_socket.send(six.b(command + '\n'))
                file_handle = unix_socket.makefile()
                data = file_handle.read().splitlines()
                return data
            except socket.timeout:
                if attempt == self.retry:
                    msg = "{} socket unavailable after {} reconnects".format(
                        self.socket_file, self.retry
                    )
                    raise socket.timeout(msg)
                time.sleep(self.retry_interval)
                continue
            # PermissionDenied is raised when socket file isn't attached to a
            # running process.
            except:
                raise
            else:
                unix_socket.close()

    def run_command(self, command, full_output=False):
        """Run a command to HAProxy process.

        :param command: A valid command to execute
        :type command: string
        :param full_output: (optional) Return all output, by default
          returns only the 1st line of the output
        :type full_output: bool
        :return: 1st line of the output or the whole output as a list
        :rtype: string or list if full_output is True
        """
        output = self.send_command(command)

        if full_output:
            return output
        else:
            return output[0]

    def proc_info(self):
        """Return a dictionary containing information about HAProxy daemon.

        :rtype: dictionary, see utils.info2dict() for details
        """
        raw_info = self.send_command('show info')

        return info2dict(raw_info)

    def stats(self):
        """Return a nested dictionary containing pool information.

        :rtype: dict, see ``utils.stat2dict`` for details on the structure
        """
        csv_data = self.send_command('show stat')
        self.hap_stats = stat2dict(csv_data)

        return self.hap_stats

    def metric(self, name):
        return converter(self.proc_info()[name])

    def pools_stats(self):
        return self.stats()['pools']

    def frontends_stats(self):
        return self.stats()['frontends']

    def servers_stats(self, pool):
        return self.stats()['pools'][pool]['servers']

    def pools(self, name=None):
        """Build _Pool objects for each pool.

        :param name: (optional) pool name, defaults to None
        :type name: string
        :return: a list of _Pool objects for each pool
        :rtype: list
        """
        pools = []
        return_list = []
        pools = self.pools_stats()
        if name is not None:
            if name in pools:
                return_list.append(_Pool(self, name))
            else:
                return return_list
        else:
            for name in pools:
                return_list.append(_Pool(self, name))

        return return_list

    def get_frontends(self, name=None):
        """Build :class:`_Frontend` objects for each frontend.

        :param name: (optional) pool name, defaults to ``None``
        :type name: ``string``
        :return: a list of :class:`_Frontend` objects for each pool
        :rtype: ``list``

        """
        frontends = []
        return_list = []
        frontends = self.frontends_stats()
        if name is not None:
            if name in frontends:
                return_list.append(_Frontend(self, name))
            else:
                return return_list
        else:
            for frontend in frontends:
                return_list.append(_Frontend(self, frontend))

        return return_list


class _Frontend(object):
    """Class for interacting with a frontend in one HAProxy process.

    :param hap_process: a :class:`_HAProxyProcess` object.
    :param name: frontend name.
    :type name: ``string``

    """
    def __init__(self, hap_process, name):
        self.hap_process = hap_process
        self._name = name
        self.hap_process_nb = self.hap_process.process_nb

    @property
    def name(self):
        """Return a string which is the name of the frontend"""
        return self._name

    @property
    def process_nb(self):
        return int(self.hap_process_nb)

    def stats(self):
        keys = self.hap_process.frontends_stats()[self.name].heads
        values = self.hap_process.frontends_stats()[self.name].parts

        return dict(zip(keys, values))

    def metric(self, name):
        """Return the value of a metric"""
        return converter(
            getattr(self.hap_process.frontends_stats()[self.name], name))

    def command(self, cmd):
        """Run command to HAProxy

        :param cmd: a valid command to execute.
        :type cmd: ``string``
        :return: 1st line of the output.
        :rtype: ``string``
        """
        return self.hap_process.run_command(cmd)


class _Pool(object):
    """Class for interacting with a pool in one HAProxy process.

    :param hap_process: a :class::`_HAProxyProcess` object.
    :param name: pool name.
    :type name: ``string``
    """
    def __init__(self, hap_process, name):
        self.hap_process = hap_process
        self._name = name
        self.hap_process_nb = self.hap_process.process_nb

    @property
    def name(self):
        """Return a string which is the name of the pool"""
        return self._name

    @property
    def process_nb(self):
        return int(self.hap_process_nb)

    def stats(self):
        """Build dictionary for all statistics reported by HAProxy.

        :return: A dictionary with statistics
        :rtype: dict
        """
        keys = self.hap_process.pools_stats()[self.name]['stats'].heads
        values = self.hap_process.pools_stats()[self.name]['stats'].parts

        return dict(zip(keys, values))

    def metric(self, name):
        return converter(
            getattr(self.hap_process.pools_stats()[self.name]['stats'], name))

    def command(self, cmd):
        return self.hap_process.run_command(cmd)

    def servers(self, name=None):
        """Return a list of _Server objects for each server of the pool.

        :param name: (optional): server name lookup, defaults to None.
        :type name: string
        """
        servers = []
        return_list = []

        servers = self.hap_process.servers_stats(self.name)
        if name is not None:
            if name in servers:
                return_list.append(_Server(self, name))
            else:
                return []
        else:
            for servername in servers:
                return_list.append(_Server(self, servername))

        return return_list


class _Server(object):
    """Class for interacting with a server of a pool in one HAProxy.

    :param pool: A _Pool object in which server is part of.
    :param name: server name.
    :type name: ``string``
    """
    def __init__(self, pool, name):
        self.pool = pool
        self._name = name
        self.process_nb = self.pool.process_nb

    @property
    def name(self):
        """Return the name of the pool server."""
        return self._name

    def metric(self, name):
        return converter(getattr(
            self.pool.hap_process.servers_stats(self.pool.name)[self.name], name))

    def stats(self):
        keys = self.pool.hap_process.servers_stats(self.pool.name)[self.name].heads
        values = self.pool.hap_process.servers_stats(self.pool.name)[self.name].parts

        return dict(zip(keys, values))

    def command(self, cmd):
        return self.pool.hap_process.run_command(cmd)
