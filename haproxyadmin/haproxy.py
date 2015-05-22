# -*- coding: utf-8 -*- #
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.haproxy
~~~~~~~~~~~~

This module implements the haproxyadmin API.

:copyright: (c) 2015 by Pavlos Parissis.
:license: Apache 2.0, see LICENSE for more details.

"""
import os
import glob

from .frontend import Frontend
from .pool import Pool
from .poolmember import PoolMember
from .utils import (is_unix_socket, cmd_across_all_procs, calculate, isint,
                    should_die, check_command, check_output)

from .internal import _HAProxyProcess


VALID_STATES = PoolMember.VALID_STATES
STATE_ENABLE = PoolMember.STATE_ENABLE
STATE_DISABLE = PoolMember.STATE_DISABLE
STATE_READY = PoolMember.STATE_READY
STATE_DRAIN = PoolMember.STATE_DRAIN
STATE_MAINT = PoolMember.STATE_MAINT
FRONTEND_METRICS = Frontend.FRONTEND_METRICS
POOL_METRICS = Pool.POOL_METRICS
SERVER_METRICS = PoolMember.SERVER_METRICS


class HAProxy(object):
    """This class provides an interface to interact with HAProxy.

    Methods:
        frontends([name]): Return a list with Frontend objects.
        frontend(name): Return a Frontend object.
        get_info(): Return a list of dictionaries holding information about
        pools([poolname]): Return a list with Pool objects.
        requests(): Return total requests for all frontends.
        each HAProxy process.

    Arguments:
        socket_dir (str): Full path of directory of the socket file(s).
        socket_file (str): Full path of a valid HAProxy socket file.
        retry (int, optional): Number of connect retries (defaults to 2).
        retry_interval (int, optional): Interval time in seconds between retries
        (defaults to 2).

    """
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

    def __init__(self, socket_dir=None,
                 socket_file=None,
                 retry=2,
                 retry_interval=2):

        self._hap_processes = []
        socket_files = []

        if socket_dir and os.path.isdir(socket_dir):
            for _file in glob.glob(os.path.join(socket_dir, '*')):
                if is_unix_socket(_file):
                    socket_files.append(_file)

        if socket_file and is_unix_socket(socket_file):
            socket_files.append(os.path.realpath(socket_file))
        if not socket_files:
            raise ValueError("Wrong value for socket")

        for so_file in socket_files:
            self._hap_processes.append(
                _HAProxyProcess(so_file, retry, retry_interval)
            )

    @should_die
    def add_acl(self, acl, pattern):
        """Add an entry into the acl.

        :param acl: acl id or a file
        :type acl: integer or a file
        :param pattern: Entry to add
        :type pattern: string
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(acl=4)
          ['0x23181c0 /static/css/', '']
          >>> hap.add_acl(acl=4, pattern='/foo/' )
          True
          >>> hap.show_acl(acl=4)
          ['0x23181c0 /static/css/', '0x238f790 /foo/', '']
        """
        if isint(acl):
            cmd = "add acl #{} {}".format(acl, pattern)
        elif os.path.isfile(acl):
            cmd = "add acl {} {}".format(acl, pattern)
        else:
            raise ValueError("Invalid input")

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def add_map(self, mapid, key, value):
        """Add an entry into the map.

        :param mapid: map id or a file
        :type mapid: integer or a file
        :param key: Key to add
        :type key: string
        :param value: Value assciated to the key
        :type value: string
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1a78b20 1 www.foo.com-1', '']
          >>> hap.add_map(0, '9', 'foo')
          True
          >>> hap.show_map(0)
          ['0x1a78b20 1 www.foo.com-1', '0x1b15c80 9 foo', '']
        """
        if isint(mapid):
            cmd = "add map #{} {} {}".format(mapid, key, value)
        elif os.path.isfile(mapid):
            cmd = "add map {} {}".format(mapid, key, value)
        else:
            raise ValueError("Invalid input")

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def clear_acl(self, acl):
        """Remove all entries from a acl.

        :param acl: acl id or a file
        :type acl: integer or a file
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
        elif os.path.isfile(acl):
            cmd = "clear acl {}".format(acl)
        else:
            raise ValueError("Invalid input")

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def clear_map(self, mapid):
        """Remove all entries from a mapid.

        :param mapid: map id or a file
        :type mapid: integer or a file
        :return: True if command succeeds otherwise False
        :rtype: bool

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
        elif os.path.isfile(mapid):
            cmd = "clear map {}".format(mapid)
        else:
            raise ValueError("Invalid input")

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def clearcounters(self, all=False):
        """Clear the max values of the statistics counters.

        :param all: (optional) Clear all statistics counters in each proxy
        (frontend & backend) and in each server. This has the same effect as
        restarting.
        :type all: bool
        :return: True if command succeeds otherwise False
        :rtype: bool
        """
        if all:
            cmd = "clear counters all"
        else:
            cmd = "clear counters"

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def del_acl(self, acl, key):
        """Delete all the acl entries from the acl corresponding to the key.

        :param acl: acl id or a file
        :type acl: integer or a file
        :param key: Key to delete
        :type key: string
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(acl=4)
          ['0x23181c0 /static/css/', '0x238f790 /foo/', '0x238f810 /bar/', '']
          >>> hap.del_acl(acl=4, key='/static/css/')
          True
          >>> hap.show_acl(acl=4)
          ['0x238f790 /foo/', '0x238f810 /bar/', '']
          >>> hap.del_acl(acl=4, key='0x238f790')
          True
          >>> hap.show_acl(acl=4)
          ['0x238f810 /bar/', '']
        """
        if key.startswith('0x'):
            key = "#{}".format(key)

        if isint(acl):
            cmd = "del acl #{} {}".format(acl, key)
        elif os.path.isfile(acl):
            cmd = "del acl {} {}".format(acl, key)
        else:
            raise ValueError("Invalid input")

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def del_map(self, mapid, key):
        """Delete all the map entries from the map corresponding to the key.

        :param mapid: map id or a file
        :type mapid: integer or a file
        :param key: Key to delete
        :type key: string
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1b15cd0 9 foo', '0x1a78980 11 bar', '']
          >>> hap.del_map(0, '0x1b15cd0')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 bar', '']
          >>> hap.add_map(0, '22', 'bar22')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 bar', '0x1b15c00 22 bar22', '']
          >>> hap.del_map(0, '22')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 bar', '']
        """
        if key.startswith('0x'):
            key = "#{}".format(key)

        if isint(mapid):
            cmd = "del map #{} {}".format(mapid, key)
        elif os.path.isfile(mapid):
            cmd = "del map {} {}".format(mapid, key)
        else:
            raise ValueError("Invalid input")

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def errors(self, iid=None):
        """Dump last known request and response errors.

        If <iid> is specified, the limit the dump to errors concerning
        either frontend or backend whose ID is <iid>.

        :param iid: (optional) ID of frontend or backend
        :type iid: integer
        :return: A list of tuples of errors per process.
        1st element of tuple is process number and 2nd element of tuple
        is a list of errors.
        :rtype: list

        """
        if iid:
            cmd = "show errors {}".format(iid)
        else:
            cmd = "show errors"

        return cmd_across_all_procs(self._hap_processes, 'run_command',
                                    cmd, True)

    def frontends(self, name=None):
        """Return a list with Frontend objects.

        Arguments:
            name (str, optional): Name of frontend, defaults to None.

        """
        return_list = []

        # store _Frontend objects for each frontend as it is reported by each
        # HAProxy process.
        # key: name of the frontend
        # value: a list of _Frontend object for the frontend for each HAProxy
        # process
        frontends_across_hap_processes = {}

        # loop over all HAProxy processes and get a list of frontend objects
        for haproxy in self._hap_processes:
            for frontend in haproxy.get_frontends(name):
                if frontend.name not in frontends_across_hap_processes:
                    frontends_across_hap_processes[frontend.name] = []
                frontends_across_hap_processes[frontend.name].append(frontend)

        # build the returned list
        for value in frontends_across_hap_processes.values():
            return_list.append(Frontend(value))

        return return_list

    def frontend(self, name):
        """ Returns a Frontend object

        Arguments:
            name (str): Frontend name.

        Raises:
            ValueError: When frontend isn't found or more than 1 frontend
            is found.

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

        :param acl: acl id or a file
        :type acl: integer or a file
        :param value: Value to lookup
        :type value: string
        :return: Matching patterns associated with ACL
        :rtype: string

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(acl=4)
          ['0x2318120 /static/js/', '0x23181c0 /static/css/', '']
          >>> hap.get_acl(acl=4, value='/foo')
          'type=beg, case=sensitive, match=no'
          >>> hap.get_acl(acl=4, value='/static/js/')
          'type=beg, case=sensitive, match=yes, idx=tree, pattern="/static/js/"'
        """
        if isint(acl):
            cmd = "get acl #{} {}".format(acl, value)
        elif os.path.isfile(acl):
            cmd = "get acl {} {}".format(acl, value)
        else:
            raise ValueError("Invalid input")

        get_results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                           cmd)
        get_info_proc1 = get_results[0][1]
        if not check_output(get_info_proc1):
            raise ValueError(get_info_proc1)

        return get_info_proc1

    @should_die
    def get_map(self, mapid, value):
        """Lookup the value in the map.

        :param mapid: map id or a file
        :type mapid: integer or a file
        :param value: Value to lookup
        :type value: string
        :return: Matching patterns associated with map
        :rtype: string

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1a78980 11 new2', '0x1b15c00 22 0', '']
          >>> hap.get_map(0, '11')
          'type=str, case=sensitive, found=yes, idx=tree, key="11", value="new2", type="str"'
          >>> hap.get_map(0, '10')
          'type=str, case=sensitive, found=no'
        """
        if isint(mapid):
            cmd = "get map #{} {}".format(mapid, value)
        elif os.path.isfile(mapid):
            cmd = "get map {} {}".format(mapid, value)
        else:
            raise ValueError("Invalid input")

        get_results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                           cmd)
        get_info_proc1 = get_results[0][1]
        if not check_output(get_info_proc1):
            raise ValueError(get_info_proc1)

        return get_info_proc1

    def info(self):
        """Dump info about haproxy status on current process.

        :return: A list of dict for each process.
        :rtype: list
        """
        return_list = []

        for haproxy in self._hap_processes:
            return_list.append(haproxy.proc_info())

        return return_list

    @property
    def maxconn(self):
        """Return the configured maximum connection allowed for frontend.

        :rtype: integer
        """
        return self.metric('Maxconn')

    def member(self, hostname, pool=None):
        """Returns a list of PoolMember objects for the given member.

        If <pool> specified then limit the lookup to the <pool>.

        :param hostname: Membername to look for
        :type hostname: string
        :param pool: (optional) Pool name to look in
        :type pool: string
        :return: A list of :class:`PoolMember <PoolMember>` objects
        :rtype: list
        """

        ret = []
        for pool in self.pools(pool):
            try:
                ret.append(pool.member(hostname))
            except ValueError:
                # lookup for an nonexistent member in pool raise VauleError
                # catch and pass as we query all pools
                pass

        if not ret:
            raise ValueError("Could not find member")

        return ret

    def members(self, pool=None):
        """Returns all available members as list of PoolMember objects.

        If <pool> specified then limit the lookup to the <pool>.

        :param pool: (optional) Pool name to look in
        :type pool: string
        :return: A list of :class:`PoolMember <PoolMember>` objects
        :rtype: list
        """

        ret = []
        for pool in self.pools(pool):
            _m = pool.members()
            ret += _m

        return ret

    def metric(self, name, calculation=True):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        METRICS_SUM and METRICS_AVG.

        Arguments:
            name (str): Metric name to retrieve.

        Raises:
            ValueError: When a given metric is not found.
        """
        if name not in HAProxy.HAPROXY_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._hap_processes]

        if calculation:
            return calculate(name, metrics)
        else:
            return metrics

    def pools(self, name=None):
        """Return a list with Pool objects.

        Arguments:
            name (str, optional): Name of the pool, defaults to None.

        """
        return_list = []

        # store _Pool objects for each pool as it is reported by each HAProxy
        # process.
        # key: name of the pool
        # value: a list of _Pool object for the pool
        pools_across_hap_processes = {}

        # loop over all HAProxy processes and get a set of pools
        for hap_process in self._hap_processes:
            # Returns object _Pool
            for pool in hap_process.pools(name):
                if pool.name not in pools_across_hap_processes:
                    pools_across_hap_processes[pool.name] = []
                pools_across_hap_processes[pool.name].append(pool)

        # build the returned list
        for pool_obj in pools_across_hap_processes.values():
            return_list.append(Pool(pool_obj))

        return return_list

    def pool(self, name):
        """ Returns a Pool object

        Arguments:
            name (str): Pool name.

        Raises:
            ValueError: When pool isn't found or more than 1 pool is found.

        """
        _pool = self.pools(name)
        if len(_pool) == 1:
            return _pool[0]
        elif len(_pool) == 0:
            raise ValueError("Could not find pool")
        else:
            raise ValueError("Found more than one pool!")

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

        :rtype: integer

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

        mapid is the #<id> or <file> returned by ``show_map``.

        :param mapid: map id or a file
        :type mapid: integer or a file
        :param key: Key to delete
        :type key: string
        :param value: Value to set for the key
        :type value: string
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(0)
          ['0x1a78980 11 9', '0x1b15c00 22 0', '']
          >>> hap.set_map(0, '11', 'new')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 new', '0x1b15c00 22 0', '']
          >>> hap.set_map(0, '0x1a78980', 'new2')
          True
          >>> hap.show_map(0)
          ['0x1a78980 11 new2', '0x1b15c00 22 0', '']
        """
        if key.startswith('0x'):
            key = "#{}".format(key)

        if isint(mapid):
            cmd = "set map #{} {} {}".format(mapid, key, value)
        elif os.path.isfile(mapid):
            cmd = "set map {} {} {}".format(mapid, key, value)
        else:
            raise ValueError("Invalid input")

        results = cmd_across_all_procs(self._hap_processes, 'run_command',
                                       cmd)

        return check_command(results)

    @should_die
    def setmaxconn(self, value):
        """Set maximum connection to the frontend.

        :param value: Value to set
        :type value: integer
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage:

           >>> from haproxyadmin import haproxy
           >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
           >>> hap.setmaxconn(5555)
           True
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set maxconn global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'run_command', cmd)

        return check_command(results)

    @should_die
    def setratelimitconn(self, value):
        """Set process-wide connection rate limit.

        Arguments:
            value (int): Rate connection limit.

        Raises:
            ValueError if value isn't an integer.

        Returns:
            'OK' if limit was set successfully otherwise and list of 2-item
            tuple containg error message received by each HAProxy process.
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set rate-limit connections global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'run_command', cmd)

        return check_command(results)

    @should_die
    def setratelimitsess(self, value):
        """Set process-wide session rate limit.

        Arguments:
            value (int): Rate connection limit.

        Raises:
            ValueError if value isn't an integer.

        Returns:
            'OK' if limit was set successfully otherwise and list of 2-item
            tuple containg error message received by each HAProxy process.
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set rate-limit sessions global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'run_command', cmd)

        return check_command(results)

    @should_die
    def setratelimitsslsess(self, value):
        """Set process-wide ssl session rate limit.

        :param value: Rate ssl session limit
        :type value: integer
        :return: True if command succeeds otherwise False
        :rtype: bool
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))
        cmd = "set rate-limit ssl-sessions global {}".format(value)

        results = cmd_across_all_procs(self._hap_processes, 'run_command', cmd)

        return check_command(results)

    @should_die
    def show_acl(self, acl=None):
        """Dump info about acls.

        Without argument, the list of all available acls is returned.
        If a acl is specified, its contents are dumped.

        :param acl: (optional) acl id or a file
        :type acl: integer or a file
        :return: A list with the acls
        :rtype: list

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_acl(acl=6)
          ['0x1d09730 ver%3A27%3Bvar%3A0', '']
          >>> hap.show_acl()
          ['# id (file) description',
          "1 () acl 'ssl_fc' file '/etc/haproxy/haproxy.cfg' line 83",
          "2 () acl 'src' file '/etc/haproxy/haproxy.cfg' line 95",
          "3 () acl 'path_beg' file '/etc/haproxy/haproxy.cfg' line 97",
          '',]
        """
        if acl is not None:
            if isint(acl):
                cmd = "show acl #{}".format(acl)
            elif os.path.isfile(acl):
                cmd = "show acl {}".format(acl)
            else:
                raise ValueError("Invalid input")
        else:
            cmd = "show acl"

        acl_info = cmd_across_all_procs(self._hap_processes, 'send_command',
                                        cmd)
        # ACL can't be different per process thus we only return the acl
        # content found in 1st process.
        acl_info_proc1 = acl_info[0][1]

        if not check_output(acl_info_proc1):
            raise ValueError(acl_info_proc1)

        return acl_info_proc1

    @should_die
    def show_map(self, mapid=None):
        """Dump info about maps.

        Without argument, the list of all available maps is returned.
        If a mapid is specified, its contents are dumped.

        :param mapid: (optional) map id or a file
        :type mapid: integer or a file
        :return: A list with the maps
        :rtype: list

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> hap.show_map(map=6)
          ['# id (file) description',
           "0 (/etc/haproxy/v-m1-bk) pattern loaded ...... line 82",
           '']
          >>> hap.show_map(0)
          ['0x1a78ab0 0 www.foo.com-0', '0x1a78b20 1 www.foo.com-1', '']
        """
        if mapid is not None:
            if isint(mapid):
                cmd = "show map #{}".format(mapid)
            elif os.path.isfile(mapid):
                cmd = "show map {}".format(mapid)
            else:
                raise ValueError("Invalid input")
        else:
            cmd = "show map"
        map_info = cmd_across_all_procs(self._hap_processes, 'send_command',
                                        cmd)
        # map can't be different per process thus we only return the map
        # content found in 1st process.
        map_info_proc1 = map_info[0][1]

        if not check_output(map_info_proc1):
            raise ValueError(map_info_proc1)

        return map_info_proc1


HAPROXY_METRICS = HAProxy.HAPROXY_METRICS
