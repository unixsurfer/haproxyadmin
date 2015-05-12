# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
from .utils import (calculate, cmd_across_all_procs, compare_values,
                    should_die, check_command)


class PoolMember(object):

    """A container for a member across several HAProxy processes

    It iterates over list of member objects for aggregating all operations.

    Arguments:
        member_per_proc (list): A list of _Pool objects of the pool for
        each process
        poolname (str): Pool name

    Methods:
        status(): Return status.
        check_status(): Return check status code.
        weight(): Return weight of pool member.
        set_state(enabled): Enable/disable a pool member.
        requests(): Return requests for pool member.

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

    def __init__(self, member_per_proc, poolname):
        self._member_per_proc = member_per_proc
        self.poolname = poolname
        self._name = self._member_per_proc[0].name

    # built-in comparison operator is adjusted
    def __eq__(self, other):
        if isinstance(other, PoolMember):
            return (self.name == other.name)
        elif isinstance(other, str):
            return (self.name == other)
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    @property
    def check_code(self):
        """Return the check code.

        :rtype: integer
        """
        values = cmd_across_all_procs(
            self._member_per_proc, 'metric', 'check_code'
        )

        return compare_values(values)

    @property
    def check_status(self):
        """Return the check status.

        :rtype: string
        """
        values = cmd_across_all_procs(
            self._member_per_proc, 'metric', 'check_status'
        )

        return compare_values(values)

    @property
    def last_status(self):
        """Return the last health check contents or textual error.

        :rtype: string
        """
        values = cmd_across_all_procs(
            self._member_per_proc, 'metric', 'last_chk'
        )

        return compare_values(values)

    @property
    def last_agent_check(self):
        """Return the last agent check contents or textual error.

        :rtype: string
        """
        values = cmd_across_all_procs(
            self._member_per_proc, 'metric', 'last_agt'
        )

        return compare_values(values)

    def metric(self, name):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        utils.METRICS_SUM and utils.METRICS_AVG.

        :param name: Metric name to retrieve
        :type name: Any of ``PoolMember.SERVER_METRICS``
        :rtype: number, integer or float
        :raise: ``ValueError`` when a given metric is not found
        """
        metrics = []
        if name not in PoolMember.SERVER_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._member_per_proc]

        return calculate(name, metrics)

    @property
    def name(self):
        """Return the name of the member.

        :rtype: string
        """
        return self._name

    @property
    def requests(self):
        """Return the number of requests.

        :rtype: integer
        """
        return self.metric('lbtot')

    def requests_per_process(self):
        """Return the number of requests for the member per process.

        :rtype: list of tuple, where 1st element is process number and 2nd
        element is requests.
        """
        results = cmd_across_all_procs(self._member_per_proc, 'metric', 'lbtot')

        return results

    @property
    def process_nb(self):
        """Return a list of process number in which pool member is configured.

        :rtype: list
        """
        process_numbers = []
        for member in self._member_per_proc:
            process_numbers.append(member.process_nb)

        return process_numbers

    @should_die
    def setstate(self, value):
        """Set the state of a member in the pool.

        The value should be any of the following
        :param value: State to set
        :type value: any of the following STATE_ constans
        * STATE_ENABLE: Mark the member UP and checks are re-enabled
        * STATE_DISABLE: Mark the member DOWN for maintenance and checks
        disabled.
        * STATE_READY: Put member in normal mode.
        * STATE_DRAIN: Remove the member from load balancing.
        * STATE_MAINT: Remove the member from load balancing and health checks
        are disabled.
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage:

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> member = hap.member('member_bkall', pool='backend_proc1')[0]
          >>> member.setstate(haproxy.STATE_DISABLE)
          True
          >>> member.status
          'MAINT'
          >>> member.setstate(haproxy.STATE_ENABLE)
          True
          >>> member.status
          'no check'
        """
        if value not in PoolMember.VALID_STATES:
            values = ', '.join(PoolMember.VALID_STATES)
            raise ValueError("Wrong value, allowed values {}".format(values))
        if value == 'enable' or value == 'disable':
            cmd = "{} server {}/{}".format(value, self.poolname, self.name)
        else:
            cmd = "set server {}/{} state {}".format(
                self.poolname, self.name, value
            )

        results = cmd_across_all_procs(self._member_per_proc, 'command', cmd)

        return check_command(results)

    def stats_per_process(self):
        """Return all stats of the member per process.

        :return: A list of tuple, where 1st element is process number and 2nd
        element is a dict
        :rtype: list
        """
        values = cmd_across_all_procs(self._member_per_proc, 'stats')

        return values

    @property
    def status(self):
        """Return the status of the member.

        :rtype: string
        :raise: :class: `IncosistentData` exception if status is different
        per process
        """
        values = cmd_across_all_procs(self._member_per_proc, 'metric', 'status')

        return compare_values(values)

    @property
    def weight(self):
        """Return the weight.

        :rtype: integer
        :raise: :class:`IncosistentData` exception if weight is different
        per process
        """
        values = cmd_across_all_procs(self._member_per_proc, 'metric', 'weight')

        return compare_values(values)

    @should_die
    def setweight(self, value):
        """Set a weight.

        If the value ends with the '%' sign, then the new weight will be
        relative to the initially configured weight.  Absolute weights
        are permitted between 0 and 256.

        :param value: Weight to set
        :type value: integer or string with '%' sign
        :return: True if command succeeds otherwise False
        :rtype: bool

        Usage:

           >>> from haproxyadmin import haproxy
           >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
           >>> member = hap.member('member_bkall', pool='backend_proc1')[0]
           >>> member.weight
           100
           >>> member.setweight('20%')
           True
           >>> member.weight
           20
           >>> member.setweight(58)
           True
           >>> member.weight
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
            cmd = "set weight {}/{} {}".format(self.poolname,
                                               self.name,
                                               value)
        else:
            raise ValueError(msg)

        results = cmd_across_all_procs(self._member_per_proc, 'command', cmd)

        return check_command(results)

    @should_die
    def shutdown(self):
        """Terminate all the sessions attached to the specified server.

        :return: True if command succeeds otherwise False
        :rtype: bool
        """

        cmd = "shutdown sessions server {}/{}".format(self.poolname, self.name)
        results = cmd_across_all_procs(self._member_per_proc, 'command', cmd)

        return check_command(results)
