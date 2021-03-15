# -*- coding: utf-8 -*- #
# pylint: disable=superfluous-parens
#

"""
haproxyadmin.haproxy
~~~~~~~~~~~~~~~~~~~~

This module implements the main haproxyadmin API.

"""
import os
import glob

from haproxyadmin.frontend import Frontend
from haproxyadmin.backend import Backend
from haproxyadmin.utils import (is_unix_socket, cmd_across_all_procs, converter,
                                calculate, isint, should_die, check_command,
                                check_output, compare_values, connected_socket)
from haproxyadmin.internal.haproxy import _HAProxyProcess
from haproxyadmin.exceptions import CommandFailed


HAPROXY_METRICS = [
    'SslFrontendMaxKeyRate',
    'Hard_maxconn',
    'SessRateLimit',
    'Process_num',
    'Memmax_MB',
    'CompressBpsRateLim',
    'MaxSslConns',
    'ConnRateLimit',
    'SslRateLimit',
    'MaxConnRate',
    'CumConns',
    'SslBackendKeyRate',
    'SslCacheLookups',
    'CurrSslConns',
    'Run_queue',
    'Maxpipes',
    'Idle_pct',
    'SslFrontendKeyRate',
    'Tasks',
    'MaxZlibMemUsage',
    'SslFrontendSessionReuse_pct',
    'CurrConns',
    'SslCacheMisses',
    'SslRate',
    'CumSslConns',
    'PipesUsed',
    'Maxconn',
    'CompressBpsIn',
    'ConnRate',
    'Ulimit-n',
    'SessRate',
    'SslBackendMaxKeyRate',
    'CumReq',
    'PipesFree',
    'ZlibMemUsage',
    'Uptime_sec',
    'CompressBpsOut',
    'Maxsock',
    'MaxSslRate',
    'MaxSessRate',
]


class HAProxy(object):
    """Build a user-created :class:`HAProxy` object for HAProxy.

    This is the main class to interact with HAProxy and provides methods
    to create objects for managing frontends, backends and servers. It also
    provides an interface to interact with HAProxy as a way to
    retrieve settings/statistics but also change settings.

    ACLs and MAPs are also managed by :class:`HAProxy` class.

    :param socket_dir: a directory with HAProxy stats files.
    :type socket_dir: ``string``
    :param socket_file: absolute path of HAProxy stats file.
    :type socket_file: ``string``
    :param retry: number of times to retry to open a UNIX socket
      connection after a failure occurred, possible values

      - None => don't retry
      - 0 => retry indefinitely
      - 1..N => times to retry

    :type retry: ``integer`` or ``None``
    :param retry_interval: sleep time between the retries.
    :type retry_interval: ``integer``
    :param timeout: timeout for the connection
    :type timeout: ``float``
    :return: a user-created :class:`HAProxy` object.
    :rtype: :class:`HAProxy`
    """

    def __init__(self,
                 socket_dir=None,
                 socket_file=None,
                 retry=2,
                 retry_interval=2,
                 timeout=1,
                 ):

        self._hap_processes = []
        socket_files = []

        if socket_dir:
            if not os.path.exists(socket_dir):
                raise ValueError("socket directory does not exist "
                                 "{}".format(socket_dir))

            for _file in glob.glob(os.path.join(socket_dir, '*')):
                if is_unix_socket(_file) and connected_socket(_file, timeout):
                    socket_files.append(_file)
        elif (socket_file and is_unix_socket(socket_file) and
              connected_socket(socket_file, timeout)):
            socket_files.append(os.path.realpath(socket_file))
        else:
            raise ValueError("UNIX socket file was not set")

        if not socket_files:
            raise ValueError("No valid UNIX socket file was found, directory: "
                             "{} file: {}".format(socket_dir, socket_file))

        for so_file in socket_files:
            self._hap_processes.append(
                _HAProxyProcess(
                    socket_file=so_file,
                    retry=retry,
                    retry_interval=retry_interval,
                    timeout=timeout
                 )
            )

    @should_die
    def add_acl(self, acl, pattern):
        """Add an entry into the acl.

        :param acl: acl id or a file.
        :type acl: ``integer`` or a file path passed as ``string``
        :param pattern: entry to add.
        :type pattern: ``string``
        :return: ``True`` if command succeeds otherwise ``False``
        :rtype: ``bool``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(acl=4)
          ['0x23181c0 /static/css/']
          >>> hap.add_acl(acl=4, pattern='/foo/' )
          True
          >>> hap.show_acl(acl=4)
          ['0x23181c0 /static/css/', '0x238f790 /foo/']
        """
        if isint(acl):
            cmd = "add acl #{} {}".format(acl, pattern)
        else:
            cmd = "add acl {} {}".format(acl, pattern)

        results = cmd_across_all_procs(self._hap_processes, 'command',
                                       cmd)

        return check_command(results)

    @should_die
    def add_map(self, mapid, key, value):
        """Add an entry into the map.

        :param mapid: map id or a file.
        :type mapid: ``integer`` or a file path passed as ``string``
        :param key: key to add.
        :type key: ``string``
        :param value: Value assciated to the key.
        :type value: ``string``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1a78b20 1 www.foo.com-1']
          >>> hap.add_map(0, '9', 'foo')
          True
          >>> hap.show_map(0)
          ['0x1a78b20 1 www.foo.com-1', '0x1b15c80 9 foo']
        """
        if isint(mapid):
            cmd = "add map #{} {} {}".format(mapid, key, value)
        else:
            cmd = "add map {} {} {}".format(mapid, key, value)

        results = cmd_across_all_procs(self._hap_processes, 'command',
                                       cmd)

        return check_command(results)

    @should_die
    def clear_acl(self, acl):
        """Remove all entries from a acl.

        :param acl: acl id or a file.
        :type acl: ``integer`` or a file path passed as ``string``
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.clear_acl(acl=4)
          True
          >>> hap.clear_acl(acl='/etc/haproxy/bl_frontend')
          True
        """
        if isint(acl):
            cmd = "clear acl #{}".format(acl)
        else:
            cmd = "clear acl {}".format(acl)

        results = cmd_across_all_procs(self._hap_processes, 'command',
                                       cmd)

        return check_command(results)

    @should_die
    def clear_map(self, mapid):
        """Remove all entries from a mapid.

        :param mapid: map id or a file
        :type mapid: ``integer`` or a file path passed as ``string``
        :return: ``True`` if command succeeds otherwise ``False``
        :rtype: ``bool``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.clear_map(0)
          True
          >>> hap.clear_map(mapid='/etc/haproxy/bl_frontend')
          True
        """
        if isint(mapid):
            cmd = "clear map #{}".format(mapid)
        else:
            cmd = "clear map {}".format(mapid)

        results = cmd_across_all_procs(self._hap_processes, 'command',
                                       cmd)

        return check_command(results)

    @should_die
    def clearcounters(self, all=False):
        """Clear the max values of the statistics counters.

        When ``all`` is set to ``True`` clears all statistics counters in
        each proxy (frontend & backend) and in each server. This has the same
        effect as restarting.

        :param all: (optional) clear all statistics counters.
        :type all: ``bool``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``
        """
        if all:
            cmd = "clear counters all"
        else:
            cmd = "clear counters"

        results = cmd_across_all_procs(self._hap_processes, 'command',
                                       cmd)

        return check_command(results)

    @property
    def totalrequests(self):
        """Return total cumulative number of requests processed by all processes.

        :rtype: ``integer``

        .. note::
           This is the total number of requests that are processed by HAProxy.
           It counts requests for frontends and backends. Don't forget that
           a single client request passes HAProxy twice.

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.totalrequests
          457
        """
        return self.metric('CumReq')

    @property
    def processids(self):
        """Return the process IDs of all HAProxy processes.

        :rtype: ``list``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.processids
          [22029, 22028, 22027, 22026]
        """
        return [x.metric('Pid') for x in self._hap_processes]

    @should_die
    def del_acl(self, acl, key):
        """Delete all the acl entries from the acl corresponding to the key.

        :param acl: acl id or a file
        :type acl: ``integer`` or a file path passed as ``string``
        :param key: key to delete.
        :type key: ``string``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(acl=4)
          ['0x23181c0 /static/css/', '0x238f790 /foo/', '0x238f810 /bar/']
          >>> hap.del_acl(acl=4, key='/static/css/')
          True
          >>> hap.show_acl(acl=4)
          ['0x238f790 /foo/', '0x238f810 /bar/']
          >>> hap.del_acl(acl=4, key='0x238f790')
          True
          >>> hap.show_acl(acl=4)
          ['0x238f810 /bar/']
        """
        if key.startswith('0x'):
            key = "#{}".format(key)

        if isint(acl):
            cmd = "del acl #{} {}".format(acl, key)
        else:
            cmd = "del acl {} {}".format(acl, key)

        results = cmd_across_all_procs(self._hap_processes, 'command',
                                       cmd)

        return check_command(results)

    @should_die
    def del_map(self, mapid, key):
        """Delete all the map entries from the map corresponding to the key.

        :param mapid: map id or a file.
        :type mapid: ``integer`` or a file path passed as ``string``.
        :param key: key to delete
        :type key: ``string``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1b15cd0 9 foo', '0x1a78980 11 bar']
          >>> hap.del_map(0, '0x1b15cd0')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 bar']
          >>> hap.add_map(0, '22', 'bar22')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 bar', '0x1b15c00 22 bar22']
          >>> hap.del_map(0, '22')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 bar']
        """
        if key.startswith('0x'):
            key = "#{}".format(key)

        if isint(mapid):
            cmd = "del map #{} {}".format(mapid, key)
        else:
            cmd = "del map {} {}".format(mapid, key)

        results = cmd_across_all_procs(self._hap_processes, 'command',
                                       cmd)

        return check_command(results)

    @should_die
    def errors(self, iid=None):
        """Dump last known request and response errors.

        If <iid> is specified, the limit the dump to errors concerning
        either frontend or backend whose ID is <iid>.

        :param iid: (optional) ID of frontend or backend.
        :type iid: integer
        :return: A list of tuples of errors per process.

          #. process number
          #. ``list`` of errors

        :rtype: ``list``
        """
        if iid:
            cmd = "show errors {}".format(iid)
        else:
            cmd = "show errors"

        return cmd_across_all_procs(self._hap_processes, 'command',
                                    cmd, full_output=True)

    def frontends(self, name=None):
        """Build a list of :class:`Frontend <haproxyadmin.frontend.Frontend>`

        :param name: (optional) frontend name to look up.
        :type name: ``string``
        :return: list of :class:`Frontend <haproxyadmin.frontend.Frontend>`.
        :rtype: ``list``
        """
        return_list = []

        # store _Frontend objects for each frontend per haproxy process.
        # key: name of the frontend
        # value: a list of _Frontend objects
        frontends_across_hap_processes = {}

        # loop over all haproxy processes and get a list of frontend objects
        for haproxy in self._hap_processes:
            for frontend in haproxy.frontends(name):
                if frontend.name not in frontends_across_hap_processes:
                    frontends_across_hap_processes[frontend.name] = []
                frontends_across_hap_processes[frontend.name].append(frontend)

        # build the returned list
        for value in frontends_across_hap_processes.values():
            return_list.append(Frontend(value))

        return return_list

    def frontend(self, name):
        """Build a :class:`Frontend <haproxyadmin.frontend.Frontend>` object.

        :param name: frontend name to look up.
        :type name: ``string``
        :return: a :class:`Frontend <haproxyadmin.frontend.Frontend>` object
          for the frontend.
        :rtype: :class:`Frontend <haproxyadmin.frontend.Frontend>`
        :raises: :class::`ValueError` when frontend isn't found or more than 1
          frontend is found.
        """
        _frontend = self.frontends(name)
        if len(_frontend) == 1:
            return _frontend[0]
        elif len(_frontend) == 0:
            raise ValueError("Could not find frontend")
        else:
            raise ValueError("Found more than one frontend!")

    @should_die
    def get_acl(self, acl, value):
        """Lookup the value in the ACL.

        :param acl: acl id or a file.
        :type acl: ``integer`` or a file path passed as ``string``
        :param value: value to lookup
        :type value: ``string``
        :return: matching patterns associated with ACL.
        :rtype: ``string``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(acl=4)
          ['0x2318120 /static/js/', '0x23181c0 /static/css/']
          >>> hap.get_acl(acl=4, value='/foo')
          'type=beg, case=sensitive, match=no'
          >>> hap.get_acl(acl=4, value='/static/js/')
          'type=beg, case=sensitive, match=yes, idx=tree, pattern="/static/js/"'
        """
        if isint(acl):
            cmd = "get acl #{} {}".format(acl, value)
        else:
            cmd = "get acl {} {}".format(acl, value)

        get_results = cmd_across_all_procs(self._hap_processes, 'command', cmd)
        get_info_proc1 = get_results[0][1]
        if not check_output(get_info_proc1):
            raise ValueError(get_info_proc1)

        return get_info_proc1

    @should_die
    def get_map(self, mapid, value):
        """Lookup the value in the map.

        :param mapid: map id or a file.
        :type mapid: ``integer`` or a file path passed as ``string``
        :param value: value to lookup.
        :type value: ``string``
        :return: matching patterns associated with map.
        :rtype: ``string``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1a78980 11 new2', '0x1b15c00 22 0']
          >>> hap.get_map(0, '11')
          'type=str, case=sensitive, found=yes, idx=tree, key="11", value="new2", type="str"'
          >>> hap.get_map(0, '10')
          'type=str, case=sensitive, found=no'
        """
        if isint(mapid):
            cmd = "get map #{} {}".format(mapid, value)
        else:
            cmd = "get map {} {}".format(mapid, value)

        get_results = cmd_across_all_procs(self._hap_processes, 'command',
                                           cmd)
        get_info_proc1 = get_results[0][1]
        if not check_output(get_info_proc1):
            raise CommandFailed(get_info_proc1[0])

        return get_info_proc1

    def info(self):
        """Dump info about haproxy stats on current process.

        :return: A list of ``dict`` for each process.
        :rtype: ``list``
        """
        return_list = []

        for haproxy in self._hap_processes:
            return_list.append(haproxy.proc_info())

        return return_list

    @property
    def maxconn(self):
        """Return the sum of configured maximum connection allowed for HAProxy.

        :rtype: ``integer``
        """
        return self.metric('Maxconn')

    def server(self, hostname, backend=None):
        """Build :class:`Server <haproxyadmin.server.Server> for a server.`
        objects for the given server.

        If ``backend`` specified then lookup is limited to that backend.

        .. note::
            If a server is member of more than 1 backend then muliple objects
            for the same server is returned.

        :param hostname: servername to look for.
        :type hostname: ``string``
        :param backend: (optional) backend name to look in.
        :type backend: ``string``
        :return: a list of :class:`Server <haproxyadmin.server.Server>`
          objects.
        :rtype: ``list``
        """
        ret = []
        for backend in self.backends(backend):
            try:
                ret.append(backend.server(hostname))
            except ValueError:
                # lookup for an nonexistent server in backend raise VauleError
                # catch and pass as we query all backends
                pass

        if not ret:
            raise ValueError("Could not find server")

        return ret

    def servers(self, backend=None):
        """Build :class:`Server <haproxyadmin.server.Server>` for each server.

        If ``backend`` specified then lookup is limited to that backend.

        :param backend: (optional) backend name.
        :type backend: ``string``
        :return: A list of :class:`Server <Server>` objects
        :rtype: ``list``.
        """
        return_list = []
        for backend in self.backends(backend):
            servers = backend.servers()
            return_list += servers

        return return_list

    def metric(self, name):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        :data:`haproxyadmin.utils.METRICS_SUM` and
        :data:`haproxyadmin.utils.METRICS_AVG`.

        :param name: metric name to retrieve
        :type name: any of :data:`haproxyadmin.haproxy.HAPROXY_METRICS`
        :return: value of the metric
        :rtype: ``integer``
        :raise: ``ValueError`` when a given metric is not found
        """
        if name not in HAPROXY_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._hap_processes]
        metrics[:] = (converter(x) for x in metrics)
        metrics[:] = (x for x in metrics if x is not None)

        return calculate(name, metrics)

    def backends(self, name=None):
        """Build a list of :class:`Backend <haproxyadmin.backend.Backend>`

        :param name: (optional) backend name to look up.
        :type name: ``string``
        :return: list of :class:`Backend <haproxyadmin.backend.Backend>`.
        :rtype: ``list``
        """
        return_list = []

        # store _Backend objects for each backend per haproxy process.
        # key: name of the backend
        # value: a list of _Backend objects
        backends_across_hap_processes = {}

        # loop over all HAProxy processes and get a set of backends
        for hap_process in self._hap_processes:
            # Returns object _Backend
            for backend in hap_process.backends(name):
                if backend.name not in backends_across_hap_processes:
                    backends_across_hap_processes[backend.name] = []
                backends_across_hap_processes[backend.name].append(backend)

        # build the returned list
        for backend_obj in backends_across_hap_processes.values():
            return_list.append(Backend(backend_obj))

        return return_list

    def backend(self, name):
        """Build a :class:`Backend <haproxyadmin.backend.Backend>` object.

        :param name: backend name to look up.
        :type name: ``string``
        :raises: :class::`ValueError` when backend isn't found or more than 1
          backend is found.
        """
        _backend = self.backends(name)
        if len(_backend) == 1:
            return _backend[0]
        elif len(_backend) == 0:
            raise ValueError("Could not find backend")
        else:
            raise ValueError("Found more than one backend!")

    @property
    def ratelimitconn(self):
        """Return the process-wide connection rate limit."""
        return self.metric('ConnRateLimit')

    @property
    def ratelimitsess(self):
        """Return the process-wide session rate limit."""
        return self.metric('SessRateLimit')

    @property
    def ratelimitsslsess(self):
        """Return the process-wide ssl session rate limit."""
        return self.metric('SslRateLimit')

    @property
    def requests(self):
        """Return total requests processed by all frontends.

        :rtype: ``integer``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.requests
          457
        """
        return sum([x.requests for x in self.frontends()])

    @should_die
    def set_map(self, mapid, key, value):
        """Modify the value corresponding to each key in a map.

        mapid is the #<id> or <file> returned by
        :func:`show_map <haproxyadmin.haproxy.HAProxy.show_map>`.

        :param mapid: map id or a file.
        :type mapid: ``integer`` or a file path passed as ``string``
        :param key: key id
        :type key: ``string``
        :param value: value to set for the key.
        :type value: ``string``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1a78980 11 9', '0x1b15c00 22 0']
          >>> hap.set_map(0, '11', 'new')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 new', '0x1b15c00 22 0']
          >>> hap.set_map(0, '0x1a78980', 'new2')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 new2', '0x1b15c00 22 0']
        """
        if key.startswith('0x'):
            key = "#{}".format(key)

        if isint(mapid):
            cmd = "set map #{} {} {}".format(mapid, key, value)
        else:
            cmd = "set map {} {} {}".format(mapid, key, value)

        results = cmd_across_all_procs(self._hap_processes, 'command', cmd)

        return check_command(results)

    @should_die
    def command(self, cmd):
        """Send a command to haproxy process.

        This allows a user to send any kind of command to
        haproxy. We **do not* perfom any sanitization on input
        and on output.

        :param cmd: a command to send to haproxy process.
        :type cmd: ``string``
        :return: list of 2-item tuple

        #. HAProxy process number
        #. what the method returned

        :rtype: ``list``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.command('show stats')
          ['0x23181c0 /static/css/']
          >>> hap.add_acl(acl=4, pattern='/foo/' )
          True
          >>> hap.show_acl(acl=4)
          ['0x23181c0 /static/css/', '0x238f790 /foo/']
        """
        return cmd_across_all_procs(self._hap_processes,
                                    'command', cmd, full_output=True)

    @should_die
    def setmaxconn(self, value):
        """Set maximum connection to the frontend.

        :param value: value to set.
        :type value: ``integer``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage:

           >>> from haproxyadmin import haproxy
           >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
           >>> hap.setmaxconn(5555)
           True
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set maxconn global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'command', cmd)

        return check_command(results)

    @should_die
    def setratelimitconn(self, value):
        """Set process-wide connection rate limit.

        :param value: rate connection limit.
        :type value: ``integer``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``
        :raises: ``ValueError`` if value is not an ``integer``.
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set rate-limit connections global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'command', cmd)

        return check_command(results)

    @should_die
    def setratelimitsess(self, value):
        """Set process-wide session rate limit.

        :param value: rate session limit.
        :type value: ``integer``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``
        :raises: ``ValueError`` if value is not an ``integer``.
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set rate-limit sessions global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'command', cmd)

        return check_command(results)

    @should_die
    def setratelimitsslsess(self, value):
        """Set process-wide ssl session rate limit.

        :param value: rate ssl session limit.
        :type value: ``integer``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``
        :raises: ``ValueError`` if value is not an ``integer``.
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set rate-limit ssl-sessions global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'command', cmd)

        return check_command(results)

    @should_die
    def show_acl(self, aclid=None):
        """Dump info about acls.

        Without argument, the list of all available acls is returned.
        If a aclid is specified, its contents are dumped.

        :param aclid: (optional) acl id or a file
        :type aclid: ``integer`` or a file path passed as ``string``
        :return: a list with the acls
        :rtype: ``list``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(aclid=6)
          ['0x1d09730 ver%3A27%3Bvar%3A0']
          >>> hap.show_acl()
          ['# id (file) description',
          "1 () acl 'ssl_fc' file '/etc/haproxy/haproxy.cfg' line 83",
          "2 () acl 'src' file '/etc/haproxy/haproxy.cfg' line 95",
          "3 () acl 'path_beg' file '/etc/haproxy/haproxy.cfg' line 97",
          ]
        """
        if aclid is not None:
            if isint(aclid):
                cmd = "show acl #{}".format(aclid)
            else:
                cmd = "show acl {}".format(aclid)
        else:
            cmd = "show acl"

        acl_info = cmd_across_all_procs(self._hap_processes, 'command',
                                        cmd,
                                        full_output=True)
        # ACL can't be different per process thus we only return the acl
        # content found in 1st process.
        acl_info_proc1 = acl_info[0][1]

        if not check_output(acl_info_proc1):
            raise CommandFailed(acl_info_proc1[0])

        if len(acl_info_proc1) == 1 and not acl_info_proc1[0]:
            return []
        else:
            return acl_info_proc1

    @should_die
    def show_map(self, mapid=None):
        """Dump info about maps.

        Without argument, the list of all available maps is returned.
        If a mapid is specified, its contents are dumped.

        :param mapid: (optional) map id or a file.
        :type mapid: ``integer`` or a file path passed as ``string``
        :return: a list with the maps.
        :rtype: ``list``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map()
          ['# id (file) description',
           "0 (/etc/haproxy/v-m1-bk) pattern loaded ...... line 82",
           ]
          >>> hap.show_map(mapid=0)
          ['0x1a78ab0 0 www.foo.com-0', '0x1a78b20 1 www.foo.com-1']
        """
        if mapid is not None:
            if isint(mapid):
                cmd = "show map #{}".format(mapid)
            else:
                cmd = "show map {}".format(mapid)
        else:
            cmd = "show map"
        map_info = cmd_across_all_procs(self._hap_processes, 'command',
                                        cmd,
                                        full_output=True)
        # map can't be different per process thus we only return the map
        # content found in 1st process.
        map_info_proc1 = map_info[0][1]

        if not check_output(map_info_proc1):
            raise CommandFailed(map_info_proc1[0])

        if len(map_info_proc1) == 1 and not map_info_proc1[0]:
            return []
        else:
            return map_info_proc1

    @property
    def uptime(self):
        """Return uptime of HAProxy process

        :rtype: string

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.uptime
          '4d 0h16m26s'
        """
        values = cmd_across_all_procs(self._hap_processes, 'metric',
                                      'Uptime')

        # Just return the uptime of the 1st process
        return values[0][1]

    @property
    def description(self):
        """Return description of HAProxy

        :rtype: ``string``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.description
          'test'
        """
        values = cmd_across_all_procs(self._hap_processes, 'metric',
                                      'description')

        return compare_values(values)

    @property
    def nodename(self):
        """Return nodename of HAProxy

        :rtype: ``string``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.nodename
          'test.foo.com'
        """
        values = cmd_across_all_procs(self._hap_processes, 'metric',
                                      'node')

        return compare_values(values)

    @property
    def uptimesec(self):
        """Return uptime of HAProxy process in seconds

        :rtype: ``integer``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.uptimesec
          346588
        """
        values = cmd_across_all_procs(self._hap_processes, 'metric',
                                      'Uptime_sec')

        # Just return the uptime of the 1st process
        return values[0][1]

    @property
    def releasedate(self):
        """Return release date of HAProxy

        :rtype: ``string``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.releasedate
          '2014/10/31'
        """
        values = cmd_across_all_procs(self._hap_processes, 'metric',
                                      'Release_date')

        return compare_values(values)

    @property
    def version(self):
        """Return version of HAProxy

        :rtype: ``string``

        Usage::
          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.version
          '1.5.8'
        """
        # If multiple version of HAProxy share the same socket directory
        # then this wil always raise IncosistentData exception.
        # TODO: Document this on README
        values = cmd_across_all_procs(self._hap_processes, 'metric', 'Version')

        return compare_values(values)
