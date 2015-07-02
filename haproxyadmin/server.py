# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.server
~~~~~~~~~~~~~~~~~~~~~~~

This module provides the :class:`Server <.Server>` class which allows to
run operation for a server.

"""
from haproxyadmin.utils import (calculate, cmd_across_all_procs, compare_values,
                                should_die, check_command)


class Server(object):
    """Build a user-created :class:`Server` for a single server.

    :param _server_per_proc: list of :class:`._Server` objects.
    :type _server_per_proc: ``list``
    :rtype: a :class:`Server`.
    """
    STATE_ENABLE = 'enable'
    STATE_DISABLE = 'disable'
    STATE_READY = 'ready'
    STATE_DRAIN = 'drain'
    STATE_MAINT = 'maint'
    VALID_STATES = [
        STATE_ENABLE,
        STATE_DISABLE,
        STATE_MAINT,
        STATE_DRAIN,
        STATE_READY,
    ]
    SERVER_METRICS = [
        'qcur',
        'qmax',
        'scur',
        'smax',
        'stot',
        'bin',
        'bout',
        'dresp',
        'econ',
        'eresp',
        'wretr',
        'wredis',
        'weight',
        'act',
        'bck',
        'chkfail',
        'chkdown',
        'lastchg',
        'downtime',
        'qlimit',
        'throttle',
        'lbtot',
        'rate',
        'rate_max',
        'check_duration',
        'hrsp_1xx',
        'hrsp_2xx',
        'hrsp_3xx',
        'hrsp_4xx',
        'hrsp_5xx',
        'hrsp_other',
        'cli_abrt',
        'srv_abrt',
        'lastsess',
        'qtime',
        'ctime',
        'rtime',
        'ttime',
    ]

    def __init__(self, server_per_proc, backendname):
        self._server_per_proc = server_per_proc
        self.backendname = backendname
        self._name = self._server_per_proc[0].name

    # built-in comparison operator is adjusted
    def __eq__(self, other):
        if isinstance(other, Server):
            return (self.name == other.name)
        elif isinstance(other, str):
            return (self.name == other)
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    @property
    def sid(self):
        """Return the unique proxy server ID of the server.

        .. note::
            Because server ID is the same across all processes,
            we return the proxy ID from the 1st process.

        :rtype: ``int``
        """
        return int(self._server_per_proc[0].sid)

    @property
    def check_code(self):
        """Return the check code.

        :rtype: ``integer``
        """
        values = cmd_across_all_procs(
            self._server_per_proc, 'metric', 'check_code'
        )

        return compare_values(values)

    @property
    def check_status(self):
        """Return the check status.

        :rtype: ``string``
        """
        values = cmd_across_all_procs(
            self._server_per_proc, 'metric', 'check_status'
        )

        return compare_values(values)

    @property
    def last_status(self):
        """Return the last health check contents or textual error.

        :rtype: ``string``
        """
        values = cmd_across_all_procs(
            self._server_per_proc, 'metric', 'last_chk'
        )

        return compare_values(values)

    @property
    def last_agent_check(self):
        """Return the last agent check contents or textual error.

        :rtype: ``string``
        """
        values = cmd_across_all_procs(
            self._server_per_proc, 'metric', 'last_agt'
        )

        return compare_values(values)

    def metric(self, name):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        :data:`haproxyadmin.utils.METRICS_SUM` and
        :data:`haproxyadmin.utils.METRICS_AVG`.

        :param name: Metric name to retrieve
        :type name: any of :data:`haproxyadmin.haproxy.SERVER_METRICS`
        :rtype: number, integer or float
        :raise: ``ValueError`` when a given metric is not found
        """
        if name not in Server.SERVER_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._server_per_proc]

        return calculate(name, metrics)

    @property
    def name(self):
        """Return the name of the server.

        :rtype: ``string``

        """
        return self._name

    @property
    def requests(self):
        """Return the number of requests.

        :rtype: ``integer``

        """
        return self.metric('stot')

    def requests_per_process(self):
        """Return the number of requests for the server per process.

        :rtype: A list of tuple, where 1st element is process number and 2nd
          element is requests.

        """
        results = cmd_across_all_procs(self._server_per_proc, 'metric', 'stot')

        return results

    @property
    def process_nb(self):
        """Return a list of process number in which backend server is configured.

        :return: a list of process numbers.
        :rtype: ``list``

        """
        process_numbers = []
        for server in self._server_per_proc:
            process_numbers.append(server.process_nb)

        return process_numbers

    @should_die
    def setstate(self, state):
        """Set the state of a server in the backend.

        State can be any of the following

          * :const:`haproxyadmin.haproxy.STATE_ENABLE`: Mark the server UP and
            checks are re-enabled
          * :const:`haproxyadmin.haproxy.STATE_DISABLE`: Mark the server DOWN
            for maintenance and checks disabled.
          * :const:`haproxyadmin.haproxy.STATE_READY`: Put server in normal
            mode.
          * :const:`haproxyadmin.haproxy.STATE_DRAIN`: Remove the server from
            load balancing.
          * :const:`haproxyadmin.haproxy.STATE_MAINT`: Remove the server from
            load balancing and health checks are disabled.

        :param state: state to set.
        :type state: ``string``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage:

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> server = hap.server('member_bkall', backend='backend_proc1')[0]
          >>> server.setstate(haproxy.STATE_DISABLE)
          True
          >>> server.status
          'MAINT'
          >>> server.setstate(haproxy.STATE_ENABLE)
          True
          >>> server.status
          'no check'

        """
        if state not in Server.VALID_STATES:
            states = ', '.join(Server.VALID_STATES)
            raise ValueError("Wrong state, allowed states {}".format(states))
        if state == 'enable' or state == 'disable':
            cmd = "{} server {}/{}".format(state, self.backendname, self.name)
        else:
            cmd = "set server {}/{} state {}".format(
                self.backendname, self.name, state
            )

        results = cmd_across_all_procs(self._server_per_proc, 'command', cmd)

        return check_command(results)

    def stats_per_process(self):
        """Return all stats of the server per process.

        :return: A list of tuple 2 elements

          #. process number
          #. a dict with all stats

        :rtype: ``list``

        """
        values = cmd_across_all_procs(self._server_per_proc, 'stats')

        return values

    @property
    def status(self):
        """Return the status of the server.

        :rtype: ``string``
        :raise: :class:`IncosistentData` exception if status is different
          per process

        """
        values = cmd_across_all_procs(self._server_per_proc, 'metric', 'status')

        return compare_values(values)

    @property
    def weight(self):
        """Return the weight.

        :rtype: ``integer``
        :raise: :class:`IncosistentData` exception if weight is different
          per process
        """
        values = cmd_across_all_procs(self._server_per_proc, 'metric', 'weight')

        return compare_values(values)

    @should_die
    def setweight(self, value):
        """Set a weight.

        If the value ends with the '%' sign, then the new weight will be
        relative to the initially configured weight.  Absolute weights
        are permitted between 0 and 256.

        :param value: Weight to set
        :type value: integer or string with '%' sign
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage:

           >>> from haproxyadmin import haproxy
           >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
           >>> server = hap.server('member_bkall', backend='backend_proc1')[0]
           >>> server.weight
           100
           >>> server.setweight('20%')
           True
           >>> server.weight
           20
           >>> server.setweight(58)
           True
           >>> server.weight
           58
        """
        msg = (
            "Invalid weight, absolute weights are permitted between 0 and "
            "256 and need to be passed as integers or relative weights "
            "are allowed when the value ends with the '%' sign pass as "
            "string"
        )
        if isinstance(value, int) and 0 <= value < 256 or (
                isinstance(value, str) and value.endswith('%')):
            cmd = "set weight {}/{} {}".format(self.backendname,
                                               self.name,
                                               value)
        else:
            raise ValueError(msg)

        results = cmd_across_all_procs(self._server_per_proc, 'command', cmd)

        return check_command(results)

    @should_die
    def shutdown(self):
        """Terminate all the sessions attached to the specified server.

        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``
        """

        cmd = "shutdown sessions server {}/{}".format(self.backendname, self.name)
        results = cmd_across_all_procs(self._server_per_proc, 'command', cmd)

        return check_command(results)
