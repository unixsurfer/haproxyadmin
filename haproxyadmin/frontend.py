# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
from .utils import (calculate, cmd_across_all_procs, compare_values,
                    check_command, should_die)


class Frontend(object):

    """A container for a frontend across several HAProxy processes.


    Arguments:
        frontend_per_proc (list): A list of _Frontend objects for the given
        frontend.

    Methods:
        disable: Disable frontend
        enable: Enable frontend
        get_metrics: Return metric names
        metric (str): Return value for the metric
        maxconn(int): Set maximum number of connections
        requests_per_process: Return requests per HAProxy process
        shutdown: Shutdown frontend
        stats_per_process: Return all stats per HAProx process
        status(): Return status of frontend

    Attributes
        maxconn: Return maximum connections limit
        name (str): Return name of the pool.
        process_nb (list): Return a list of HAProxy process number in which
        frontend is configured.
        requests (int): Return number of HTTP requests served by frontend.
    """
    FRONTEND_METRICS = [
        'bin',
        'bout',
        'comp_byp',
        'comp_in',
        'comp_out',
        'comp_rsp',
        'dreq',
        'dresp',
        'ereq',
        'hrsp_1xx',
        'hrsp_2xx',
        'hrsp_3xx',
        'hrsp_4xx',
        'hrsp_5xx',
        'hrsp_other',
        'rate',
        'rate_lim',
        'rate_max',
        'req_rate',
        'req_rate_max',
        'req_tot',
        'scur',
        'slim',
        'smax',
        'stot',
    ]

    def __init__(self, frontend_per_proc):
        self._frontend_per_proc = frontend_per_proc
        self._name = self._frontend_per_proc[0].name

    # built-in comparison operator is adjusted to support
    # if 'x' in list_of_frontend_obj
    # x == frontend_obj
    def __eq__(self, other):
        if isinstance(other, Frontend):
            return (self.name == other.name)
        elif isinstance(other, str):
            return (self.name == other)
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    @should_die
    def disable(self):
        """Disable frontend.

        :param die: If ``True`` raises CommandFailed or
        MultipleCommandResults when something bad happens otherwise returns
        ``False``.
        :type die: bool
        :return: ``True`` if frontend is disabled.
        :rtype: bool
        :raise: :class:``CommandFailed`` or :class:``MultipleCommandResults``
        when ``die`` is ``True`` and something bad happens
        """
        cmd = "disable frontend {}".format(self.name)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    @should_die
    def enable(self):
        """Enable frontend."""
        cmd = "enable frontend {}".format(self.name)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    def metric(self, name):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        utils.METRICS_SUM and utils.METRICS_AVG.

        :param name: Metric name to retrieve
        :type name: Any of ``Frontend.Frontend_METRICS``
        :return: Value of the metric
        :rtype: number, integer or float
        :raise: ``ValueError`` when a given metric is not found
        """
        if name not in Frontend.FRONTEND_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._frontend_per_proc]

        return calculate(name, metrics)

    @property
    def maxconn(self):
        """Return the configured maximum connection allowed for frontend.

        :rtype: integer
        """
        return self.metric('slim')

    @should_die
    def setmaxconn(self, value):
        """Set maximum connection to the frontend.

        :param value: Max connection value
        :type value: integer
        :return: ``True`` if value was set
        :rtype: bool
        :raise: :class:``CommandFailed`` or :class:``MultipleCommandResults``
        when ``die`` is ``True`` and something bad happens
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))

        cmd = "set maxconn frontend {} {}".format(self.name, value)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    @property
    def name(self):
        """Return the name of the frontend.

        :rtype: string
        """
        return self._name

    @property
    def process_nb(self):
        """Return a list of process number in which frontend is configured.

        :rtype: list
        """
        process_numbers = []
        for frontend in self._frontend_per_proc:
            process_numbers.append(frontend.process_nb)

        return process_numbers

    @property
    def requests(self):
        """Return the number of requests.

        :rtype: integer
        """
        return self.metric('req_tot')

    def requests_per_process(self):
        """Return the number of requests for the frontend per process.

        :rtype: A list of tuple, where 1st element is process number and 2nd
        element is requests.
        """
        results = cmd_across_all_procs(self._frontend_per_proc, 'metric',
                                       'req_tot')

        return results

    @should_die
    def shutdown(self):
        """Disable the frontend.

        :rtype: bool
        """
        cmd = "shutdown frontend {}".format(self.name)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    def stats_per_process(self):
        """Return all stats of the frontend per process.

        :return: A list of tuple, where 1st element is process number and 2nd
        element is a dict
        :rtype: list
        """
        results = cmd_across_all_procs(self._frontend_per_proc, 'stats')

        return results

    @property
    def status(self):
        """Return the status of the frontend.

        :rtype: string
        :raise: :class: `IncosistentData` exception if status is different
        per process
        """
        results = cmd_across_all_procs(self._frontend_per_proc, 'metric',
                                       'status')

        return compare_values(results)
