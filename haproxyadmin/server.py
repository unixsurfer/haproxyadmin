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
                                should_die, check_command, converter,
                                check_command_addr_port, elements_of_list_same)
from haproxyadmin.exceptions import IncosistentData


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
    'act',
    'bck',
    'bin',
    'bout',
    'check_duration',
    'chkdown',
    'chkfail',
    'cli_abrt',
    'ctime',
    'downtime',
    'dresp',
    'econ',
    'eresp',
    'hrsp_1xx',
    'hrsp_2xx',
    'hrsp_3xx',
    'hrsp_4xx',
    'hrsp_5xx',
    'hrsp_other',
    'lastchg',
    'lastsess',
    'lbtot',
    'qcur',
    'qlimit',
    'qmax',
    'qtime',
    'rate',
    'rate_max',
    'rtime',
    'scur',
    'slim',
    'smax',
    'srv_abrt',
    'stot',
    'throttle',
    'ttime',
    'weight',
    'wredis',
    'wretr',
]


class Server:
    """Build a user-created :class:`Server` for a single server.

    :param _server_per_proc: list of :class:`._Server` objects.
    :type _server_per_proc: ``list``
    :rtype: a :class:`Server`.
    """

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
    def port(self):
        """The assigned port of server.

        :getter: :rtype: ``string``
        :setter:
          :param port: port to set.
          :type port: ``string``
          :rtype: ``bool``
        """
        values = cmd_across_all_procs(
            self._server_per_proc, 'metric', 'addr'
        )

        try:
            value = compare_values(values)
        except IncosistentData as exc:
            # haproxy returns address:port and compare_values() may raise
            # IncosistentData exception because assigned address is different
            # per process and not the assigned port.
            # Since we want to report the port, we simply catch that case and
            # report the assigned port.
            ports_across_proc = [value[1].split(':')[1] for value in values]
            if not elements_of_list_same(ports_across_proc):
                raise exc
            else:
                return ports_across_proc[0]
        else:
            return value.split(':')[1]

    @port.setter
    def port(self, port):
        """Set server's port."""
        cmd = "set server {}/{} addr {} port {}".format(
            self.backendname, self.name, self.address, port
        )
        results = cmd_across_all_procs(self._server_per_proc, 'command', cmd)

        return check_command_addr_port('port', results)

    @property
    def address(self):
        """The assigned address of server.

        :getter: :rtype: ``string``
        :setter:
          :param address: address to set.
          :type address: ``string``
          :rtype: ``bool``
        """
        values = cmd_across_all_procs(
            self._server_per_proc, 'metric', 'addr'
        )

        try:
            value = compare_values(values)
        except IncosistentData as exc:
            # haproxy returns address:port and compare_values() may raise
            # IncosistentData exception because assigned port is different
            # per process and not the assigned address.
            # Since we want to report the address, we simply catch that case
            # and report the assigned address.
            addr_across_proc = [value[1].split(':')[0] for value in values]
            if not elements_of_list_same(addr_across_proc):
                raise exc
            else:
                return addr_across_proc[0]
        else:
            return value.split(':')[0]

    @address.setter
    def address(self, address):
        """Set server's address."""
        cmd = "set server {}/{} addr {}".format(
            self.backendname, self.name, address
        )
        results = cmd_across_all_procs(self._server_per_proc, 'command', cmd)

        return check_command_addr_port('addr', results)

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

        :param name: The name of the metric
        :type name: any of :data:`haproxyadmin.haproxy.SERVER_METRICS`
        :rtype: number, integer
        :raise: ``ValueError`` when a given metric is not found
        """
        if name not in SERVER_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._server_per_proc]
        # num_metrics = filter(None, map(converter, metrics))
        metrics[:] = (converter(x) for x in metrics)
        metrics[:] = (x for x in metrics if x is not None)

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

          * :const:`haproxyadmin.STATE_ENABLE`: Mark the server UP and
            checks are re-enabled
          * :const:`haproxyadmin.STATE_DISABLE`: Mark the server DOWN
            for maintenance and checks disabled.
          * :const:`haproxyadmin.STATE_READY`: Put server in normal
            mode.
          * :const:`haproxyadmin.STATE_DRAIN`: Remove the server from
            load balancing.
          * :const:`haproxyadmin.STATE_MAINT`: Remove the server from
            load balancing and health checks are disabled.

        :param state: state to set.
        :type state: ``string``
        :return: ``True`` if command succeeds otherwise ``False``.
        :rtype: ``bool``

        Usage:

          >>> from haproxyadmin import haproxy, STATE_DISABLE, STATE_ENABLE
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
        if state not in VALID_STATES:
            states = ', '.join(VALID_STATES)
            raise ValueError("Wrong state, allowed states {}".format(states))
        if state in ('enable', 'disable'):
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

        cmd = "shutdown sessions server {b}/{s}".format(b=self.backendname,
                                                        s=self.name)
        results = cmd_across_all_procs(self._server_per_proc, 'command', cmd)

        return check_command(results)
