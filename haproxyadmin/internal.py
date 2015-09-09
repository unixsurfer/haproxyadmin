# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.internal
~~~~~~~~~~~~~~~~~~~~~

This module provides classes that are used within haproxyadmin for creating
objects to work with frontend, backend and server which associated with
with a single HAProxy process.

"""

import six
import socket
import time
import psutil

from haproxyadmin.utils import (info2dict, converter, stat2dict)
from haproxyadmin.exceptions import (SocketTransportError, SocketTimeout,
                                     SocketConnectionError)


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
        self.process_nb = self.metric('Process_num')
        # process id associated with this process
        self.pid = self.metric('Pid')
        self.process_create_time = psutil.Process(self.pid).create_time()

    def send_command(self, command):
        """Send a command to HAProxy over UNIX stats socket.

        :param command: A valid command to execute
        :type command: string
        :return: Output. Newline character is stripped off.
        :rtype: list
        """
        data = []
        for attempt in range(1, self.retry + 1):
            try:
                unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                # I haven't seen a case where a running process which holds a
                # UNIX socket will take more than few nanoseconds to accept a
                # connection. But, I have seen cases where it takes ~0.5secs
                # to get a respone from the socket.
                # Thus I hard-code a timeout of 0.5ms
                # TODO: consider having a configuration file for it
                unix_socket.settimeout(0.5)
                unix_socket.connect(self.socket_file)
                unix_socket.send(six.b(command + '\n'))
                file_handle = unix_socket.makefile()
                data = file_handle.read().splitlines()
            except ConnectionRefusedError:
                raise SocketConnectionError(self.socket_file)
            except socket.timeout:
                if attempt == self.retry:
                    msg = "{} socket timeout after {} reconnects".format(
                        self.socket_file, self.retry
                    )
                    raise SocketTimeout(message=msg,
                                        socket_file=self.socket_file)
                time.sleep(self.retry_interval)
                continue
            except OSError as error:
                # while stress testing HAProxy and querying for all frontend
                # metrics I get:
                # OSError: [Errno 106] Transport endpoint is already connected
                # catch this one only and reraise it withour exception
                if error.errno == 106:
                    raise SocketTransportError(message=str(error),
                                               socket_file=self.socket_file)
                else:
                    raise
            else:
                # HAProxy always send an empty string at the end
                # we remove it as it adds noise for things like ACL/MAP and etc
                # We only do that when we get more than 1 line, which only
                # happens when we ask for ACL/MAP/etc and not for giving cmds
                # such as disable/enable server
                if len(data) > 1 and data[-1] == '':
                    data.pop()
                # get out from the retry loop
                break
            finally:
                unix_socket.close()

        return data

    def reloaded(self):
        """Return ``True`` if process was reloaded otherwise ``False``."""
        current_pid = self.metric('Pid')
        current_process_create_time = psutil.Process(current_pid).create_time()

        if self.process_create_time == current_process_create_time:
            return False
        else:
            self.pid = current_pid
            self.process_create_time = current_process_create_time
            return True

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

    def stats(self, iid=-1, obj_type=-1, sid=-1):
        """Return a nested dictionary containing backend information.

        :param iid: unique proxy id, applicable for frontends and backends.
        :type iid: ``string``
        :param obj_type: selects the type of dumpable objects

            - 1 for frontends
            - 2 for backends
            - 4 for servers
            - -1 for everything.

            These values can be ORed, for example:

            1 + 2     = 3   -> frontend + backend.
            1 + 2 + 4 = 7   -> frontend + backend + server.
        :type obj_type: ``integer``
        :param sid: a server ID, -1 to dump everything.
        :type sid: ``integer``
        :rtype: dict, see ``utils.stat2dict`` for details on the structure
        """
        csv_data = self.send_command('show stat {} {} {}'.format(iid,
                                                                 obj_type,
                                                                 sid))
        self.hap_stats = stat2dict(csv_data)
        return self.hap_stats

    def metric(self, name):
        return converter(self.proc_info()[name])

    def backends_stats(self, iid=-1):
        """Build the data structure for backends

        If ``iid`` is set then builds a structure only for the particul
        backend.

        :param iid: (optinal) unique proxy id of a backend.
        :type iid: ``string``
        :retur: a dictinary with backend information.
        :rtype: ``dict``
        """
        return self.stats(iid, obj_type=2)['backends']

    def frontends_stats(self, iid=-1):
        """Build the data structure for frontends

        If ``iid`` is set then builds a structure only for the particul
        frontend.

        :param iid: (optinal) unique proxy id of a frontend.
        :type iid: ``string``
        :retur: a dictinary with frontend information.
        :rtype: ``dict``
        """
        return self.stats(iid, obj_type=1)['frontends']

    def servers_stats(self, backend, iid=-1, sid=-1):
        return self.stats(iid=iid,
                          obj_type=6,
                          sid=sid)['backends'][backend]['servers']

    def backends(self, name=None):
        """Build _backend objects for each backend.

        :param name: (optional) backend name, defaults to None
        :type name: string
        :return: a list of _backend objects for each backend
        :rtype: list
        """
        backends = []
        return_list = []
        backends = self.backends_stats()
        if name is not None:
            if name in backends:
                return_list.append(_Backend(self,
                                            name,
                                            backends[name]['stats'].iid))
            else:
                return return_list
        else:
            for name in backends:
                return_list.append(_Backend(self,
                                            name,
                                            backends[name]['stats'].iid))

        return return_list

    def frontends(self, name=None):
        """Build :class:`_Frontend` objects for each frontend.

        :param name: (optional) backend name, defaults to ``None``
        :type name: ``string``
        :return: a list of :class:`_Frontend` objects for each backend
        :rtype: ``list``
        """
        frontends = []
        return_list = []
        frontends = self.frontends_stats()
        if name is not None:
            if name in frontends:
                return_list.append(_Frontend(self,
                                             name,
                                             frontends[name].iid))
            else:
                return return_list
        else:
            for frontend in frontends:
                return_list.append(_Frontend(self,
                                             frontend,
                                             frontends[frontend].iid))

        return return_list


class _Frontend(object):
    """Class for interacting with a frontend in one HAProxy process.

    :param hap_process: a :class:`_HAProxyProcess` object.
    :param name: frontend name.
    :type name: ``string``
    :param iid: unique proxy id of the frontend.
    :type iid: ``integer``
    """
    def __init__(self, hap_process, name, iid):
        self.hap_process = hap_process
        self._name = name
        self.hap_process_nb = self.hap_process.process_nb
        self._iid = iid

    @property
    def name(self):
        """Return a string which is the name of the frontend"""
        return self._name

    @property
    def iid(self):
        """Return Proxy ID"""
        self.update_iid()

        return self._iid

    @property
    def process_nb(self):
        return int(self.hap_process_nb)

    def update_iid(self):
        if self.hap_process.reloaded():
            self._iid = getattr(self.hap_process.frontends_stats()[self.name],
                                'iid')

    def stats(self):
        self.update_iid()
        keys = self.hap_process.frontends_stats(self.iid)[self.name].heads
        values = self.hap_process.frontends_stats(self.iid)[self.name].parts

        return dict(zip(keys, values))

    def metric(self, name):
        """Return the value of a metric"""
        self.update_iid()
        return converter(
            getattr(self.hap_process.frontends_stats(self.iid)[self.name],
                    name)
        )

    def command(self, cmd):
        """Run command to HAProxy

        :param cmd: a valid command to execute.
        :type cmd: ``string``
        :return: 1st line of the output.
        :rtype: ``string``
        """
        return self.hap_process.run_command(cmd)


class _Backend(object):
    """Class for interacting with a backend in one HAProxy process.

    :param hap_process: a :class::`_HAProxyProcess` object.
    :param name: backend name.
    :type name: ``string``
    :param iid: unique proxy id of the backend.
    :type iid: ``integer``
    """
    def __init__(self, hap_process, name, iid):
        self.hap_process = hap_process
        self._name = name
        self.hap_process_nb = self.hap_process.process_nb
        self._iid = iid

    @property
    def name(self):
        """Return a string which is the name of the backend"""
        return self._name

    @property
    def iid(self):
        """Return Proxy ID"""
        self.update_iid()

        return self._iid

    @property
    def process_nb(self):
        return int(self.hap_process_nb)

    def update_iid(self):
        if self.hap_process.reloaded():
            self._iid = getattr(
                self.hap_process.backends_stats()[self.name]['stats'], 'iid')

    def stats(self):
        """Build dictionary for all statistics reported by HAProxy.

        :return: A dictionary with statistics
        :rtype: ``dict``
        """
        self.update_iid()
        keys = self.hap_process.backends_stats(self.iid)[self.name]['stats'].heads
        values = self.hap_process.backends_stats(self.iid)[self.name]['stats'].parts

        return dict(zip(keys, values))

    def metric(self, name):
        self.update_iid()
        return converter(getattr(
            self.hap_process.backends_stats(self.iid)[self.name]['stats'],
            name))

    def command(self, cmd):
        return self.hap_process.run_command(cmd)

    def servers(self, name=None):
        """Return a list of _Server objects for each server of the backend.

        :param name: (optional): server name lookup, defaults to None.
        :type name: string
        """
        servers = []
        return_list = []

        self.update_iid()
        servers = self.hap_process.servers_stats(self.name, self.iid)
        if name is not None:
            if name in servers:
                return_list.append(_Server(self,
                                           name,
                                           servers[name].sid))
            else:
                return []
        else:
            for name in servers:
                return_list.append(_Server(self,
                                           name,
                                           servers[name].sid))

        return return_list


class _Server(object):
    """Class for interacting with a server of a backend in one HAProxy.

    :param backend: a _Backend object in which server is part of.
    :param name: server name.
    :type name: ``string``
    :param sid: server id (unique inside a proxy).
    :type sid: ``string``
    """
    def __init__(self, backend, name, sid):
        self.backend = backend
        self._name = name
        self.process_nb = self.backend.process_nb
        self._sid = sid

    @property
    def name(self):
        """Return the name of the backend server."""
        return self._name

    @property
    def sid(self):
        """Return server id"""
        self.update_sid()

        return self._sid

    def update_sid(self):
        if self.backend.hap_process.reloaded():
            self._sid = getattr(
                self.backend.hap_process.servers_stats(self.backend.name)[self.name],
                'sid')

    def metric(self, name):
        self.update_sid()
        return converter(getattr(
            self.backend.hap_process.servers_stats(self.backend.name,
                                                   self.backend.iid,
                                                   self.sid)[self.name], name))

    def stats(self):
        self.update_sid()
        keys = self.backend.hap_process.servers_stats(self.backend.name)[self.name].heads
        values = self.backend.hap_process.servers_stats(self.backend.name)[self.name].parts

        return dict(zip(keys, values))

    def command(self, cmd):
        return self.backend.hap_process.run_command(cmd)
