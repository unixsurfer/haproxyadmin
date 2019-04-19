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
import errno
import time
import six

from haproxyadmin.utils import (info2dict, stat2dict)
from haproxyadmin.exceptions import (SocketTransportError, SocketTimeout,
                                     SocketConnectionError)
from haproxyadmin.internal.frontend import _Frontend
from haproxyadmin.internal.backend import _Backend


class _HAProxyProcess:
    """An object to a single HAProxy process.

    It acts as a communication pipe between the caller and individual
    HAProxy process using UNIX stats socket.

    :param socket_file: Full path of socket file.
    :type socket_file: ``string``
    :param retry: (optional) Number of connect retries (defaults to 3)
    :type retry: ``integer``
    :param retry_interval: (optional) Interval time in seconds between retries
                           (defaults to 2)
    :param timeout: timeout for the connection
    :type timeout: ``float``
    :type retry_interval: ``integer``
    """
    def __init__(self, socket_file, retry=3, retry_interval=2, timeout=1):
        self.socket_file = socket_file
        self.hap_stats = {}
        self.hap_info = {}
        self.retry = retry
        self.retry_interval = retry_interval
        self.timeout = timeout
        # process number associated with this object
        self.process_nb = self.metric('Process_num')

    def command(self, command, full_output=False):
        """Send a command to HAProxy over UNIX stats socket.

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
        raised = None  # hold possible exception raised during connect phase
        attempt = 0 # times to attempt to connect after a connection failure
        if self.retry == 0:
            # 0 means retry indefinitely
            attempt = -1
        elif self.retry is None:
            # None means don't retry
            attempt = 1
        else:
            # any other value means retry N times
            attempt = self.retry + 1
        while attempt != 0:
            try:
                unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                unix_socket.settimeout(self.timeout)
                unix_socket.connect(self.socket_file)
                unix_socket.send(six.b(command + '\n'))
                file_handle = unix_socket.makefile()
                data = file_handle.read().splitlines()
            except socket.timeout:
                raised = SocketTimeout(socket_file=self.socket_file)
            except OSError as exc:
                # while stress testing HAProxy and querying for all frontend
                # metrics I sometimes get:
                # OSError: [Errno 106] Transport endpoint is already connected
                # catch this one only and reraise it withour exception
                if exc.errno == errno.EISCONN:
                    raised = SocketTransportError(socket_file=self.socket_file)
                elif exc.errno == errno.ECONNREFUSED:
                    raised = SocketConnectionError(self.socket_file)
                else:
                    # for the rest of OSError exceptions just reraise them
                    raised = exc
            else:
                # HAProxy always send an empty string at the end
                # we remove it as it adds noise for things like ACL/MAP and etc
                # We only do that when we get more than 1 line, which only
                # happens when we ask for ACL/MAP/etc and not for giving cmds
                # such as disable/enable server
                if len(data) > 1 and data[-1] == '':
                    data.pop()
                # make sure possible previous errors are cleared
                raised = None
                # get out from the retry loop
                break
            finally:
                unix_socket.close()
                if raised:
                    time.sleep(self.retry_interval)

            attempt -= 1

        if raised:
            raise raised
        elif data:
            if full_output:
                return data
            else:
                return data[0]
        else:
            raise ValueError("no data returned from socket {}".format(
                self.socket_file))

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
        self.hap_stats = stat2dict(csv_data)
        return self.hap_stats

    def metric(self, name):
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
