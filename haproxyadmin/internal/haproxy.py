# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.internal.haproxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the main class that is used within haproxyadmin for creating
object to work with a single HAProxy process. All other internal classes use
this class to send commands to HAProxy process.

"""

import socket
import time
import six

from haproxyadmin.utils import (info2dict, stat2dict)
from haproxyadmin.internal.frontend import _Frontend
from haproxyadmin.internal.backend import _Backend
from haproxyadmin.exceptions import HAProxySocketError, SocketApplicationError


class _HAProxyProcess:
    """An object to a single HAProxy process.

    It acts as a communication pipe between the caller and individual
    HAProxy process using UNIX stats socket.

    :param socket_file: Either the full path of the UNIX socket or a tuple with
        two elements, where 1st element is the host and the second is the port.
    :type socket_file: ``string`` or ``tuple``
    :param retry: (optional) Number of connect retries (defaults to 3)
    :type retry: ``integer``
    :param retry_interval: (optional) Interval time in seconds between retries
                           (defaults to 2)
    :param timeout: timeout for the connection
    :type timeout: ``float``
    :type retry_interval: ``integer``
    """
    def __init__(
            self,
            address=None,
            retry=3,
            retry_interval=2,
            timeout=1,
        ):
        self.hap_stats = {}
        self.hap_info = {}
        self.address = address
        self.retry = retry
        self.retry_interval = retry_interval
        self.timeout = timeout
        # We pass ourselves to our custom exceptions, which use our modified
        # __str__ and our string representation needs process number, but we
        # may not have it yet as we failed to connect. Thus we must first set
        # to None.
        self.process_number = None
        try:
            _name = self.metric('Name')
        except KeyError:
            raise SocketApplicationError(self)
        else:
            if _name != "HAProxy":
                raise SocketApplicationError(self)

        self.process_number = self.metric('Process_num')


    def __repr__(self):
        return "_HAProxyProcess({!r}, {!r}, {!r}, {!r})".format(
            self.address, self.retry, self.retry_interval, self.timeout)

    def __str__(self):
        if isinstance(self.address, str):
            _str = "HAProxy server: UNIX socket {} process number {}".format(
                self.address, self.process_number)
        else:
            _str = "HAProxy server: address {}:{} process number {}".format(
                self.address[0], self.address[1], self.process_number)

        return _str

    def command(self, command, full_output=False):
        """Send a command to HAProxy.

        Newline character returned from haproxy is stripped off.

        :param command: A valid command to execute
        :type command: string
        :param full_output: (optional) Return all output, by default
          returns only the 1st line of the output
        :type full_output: ``bool``
        :return: 1st line of the output or the whole output as a list
        :rtype: ``string`` or ``list`` if full_output is True
        """
        data = []  # hold data returned from socket
        error = None
        attempt = 0 # times to attempt to connect after a connection failure

        if isinstance(self.address, str):
            hap_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        elif isinstance(self.address, tuple):
            hap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            ValueError("wrong value for address")

        hap_socket.settimeout(self.timeout)

        if self.retry == 0:  # 0 means retry indefinitely
            attempt = -1
        elif self.retry is None:  # None means don't retry
            attempt = 1
        else:  # any other value means retry N times
            attempt = self.retry + 1

        while attempt != 0:
            if error is not None:
                time.sleep(self.retry_interval)
            try:
                hap_socket.connect(self.address)
            except socket.timeout as exc:
                error = HAProxySocketError(message=exc,
                                           haproxy_server=self.haproxy_server)
            except OSError as exc:
                error = HAProxySocketError(message=exc,
                                           haproxy_server=self)
            else:
                try:
                    hap_socket.send(six.b(command + '\n'))
                    file_handle = hap_socket.makefile()
                    data = file_handle.read().splitlines()
                except socket.timeout as exc:
                    # error = "{}: {}".format(exc, socket_info)
                    error = HAProxySocketError(message=exc,
                                               haproxy_server=self.haproxy_server)
                except OSError as exc:
                    # error = "{}: {}".format(exc, socket_info)
                    error = HAProxySocketError(message=exc,
                                               haproxy_server=self.haproxy_server)
                else:
                    # HAProxy always send an empty string at the end
                    # we remove it as it adds noise for things like ACL/MAP
                    # and etc. We only do that when we get more than 1 line,
                    # which only happens when we ask for ACL/MAP/etc and not
                    # for giving cmds such as disable/enable server.
                    if len(data) > 1 and data[-1] == '':
                        data.pop()
                    error = None  # clear possible previous errors
                    hap_socket.close()
                    break

            attempt -= 1

        if error is not None:
            raise error

        if not full_output:
            return data[0]
        else:
            return data

    def proc_info(self):
        """Return a dictionary containing information about HAProxy daemon.

        :rtype: dictionary, see utils.info2dict() for details
        """
        raw_info = self.command('show info', full_output=True)

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
        csv_data = self.command('show stat {i} {o} {s}'.format(i=iid,
                                                               o=obj_type,
                                                               s=sid),
                                full_output=True)
        # self.hap_stats = stat2dict(csv_data)

        return stat2dict(csv_data)

    def metric(self, name):
        """Return the value of a metric."""
        return self.proc_info()[name]

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

        If ``iid`` is set then builds a structure only for the particular
        frontend.

        :param iid: (optinal) unique proxy id of a frontend.
        :type iid: ``string``
        :retur: a dictinary with frontend information.
        :rtype: ``dict``
        """
        return self.stats(iid, obj_type=1)['frontends']

    def servers_stats(self, backend, iid=-1, sid=-1):
        """Build the data structure for servers

        If ``iid`` is set then it builds a structure only for server, which are
        members of the particular backend and if ``sid`` is set then it builds
        the structure for that particular server.

        :param iid: (optinal) unique proxy id of a backend.
        :type iid: ``string``
        :param iid: (optinal) unique server id.
        :type iid: ``string``
        :retur: a dictinary with backend information.
        :rtype: ``dict``
        """
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
            for backend in backends:
                return_list.append(_Backend(self,
                                            backend,
                                            backends[backend]['stats'].iid))

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
