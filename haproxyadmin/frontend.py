# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.frontend
~~~~~~~~~~~~~~~~~~~~~

This module provides the :class:`Frontend <.Frontend>` class. This class can
be used to run operations on a frontend and retrieve statistics.

"""
from haproxyadmin.utils import (calculate, cmd_across_all_procs, converter,
                                check_command, should_die, compare_values)


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


class Frontend(object):
    """Build a user-created :class:`Frontend` for a single frontend.

    :param frontend_per_proc: list of :class:`._Frontend` objects.
    :type frontend_per_proc: ``list``
    :rtype: a :class:`Frontend`.
    """

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

    @property
    def iid(self):
        """Return the unique proxy ID of the frontend.

        .. note::
            Because proxy ID is the same across all processes,
            we return the proxy ID from the 1st process.

        :rtype: ``int``
        """
        return int(self._frontend_per_proc[0].iid)

    @should_die
    def disable(self):
        """Disable frontend.

        :param die: control the handling of errors.
        :type die: ``bool``
        :return: ``True`` if frontend is disabled otherwise ``False``.
        :rtype: bool
        :raise: If ``die`` is ``True``
          :class:`haproxyadmin.exceptions.CommandFailed` or
          :class:`haproxyadmin.exceptions.MultipleCommandResults` is raised
          when something bad happens otherwise returns ``False``.

        """
        cmd = "disable frontend {}".format(self.name)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    @should_die
    def enable(self):
        """Enable frontend.

        :param die: control the handling of errors.
        :type die: ``bool``
        :return: ``True`` if frontend is enabled otherwise ``False``.
        :rtype: bool
        :raise: If ``die`` is ``True``
          :class:`haproxyadmin.exceptions.CommandFailed` or
          :class:`haproxyadmin.exceptions.MultipleCommandResults` is raised
          when something bad happens otherwise returns ``False``.
        """
        cmd = "enable frontend {}".format(self.name)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    def metric(self, name):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        :data:`haproxyadmin.utils.METRICS_SUM` and
        :data:`haproxyadmin.utils.METRICS_AVG`.

        :param name: metric name to retrieve
        :type name: any of :data:`haproxyadmin.haproxy.FRONTEND_METRICS`
        :return: value of the metric
        :rtype: ``integer``
        :raise: ``ValueError`` when a given metric is not found
        """
        if name not in FRONTEND_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._frontend_per_proc]
        metrics[:] = (converter(x) for x in metrics)
        metrics[:] = (x for x in metrics if x is not None)

        return calculate(name, metrics)

    @property
    def maxconn(self):
        """Return the configured maximum connection allowed for frontend.

        :rtype: ``integer``
        """
        return self.metric('slim')

    @should_die
    def setmaxconn(self, value):
        """Set maximum connection to the frontend.

        :param die: control the handling of errors.
        :type die: ``bool``
        :param value: max connection value.
        :type value: ``integer``
        :return: ``True`` if value was set.
        :rtype: ``bool``
        :raise: If ``die`` is ``True``
          :class:`haproxyadmin.exceptions.CommandFailed` or
          :class:`haproxyadmin.exceptions.MultipleCommandResults` is raised
          when something bad happens otherwise returns ``False``.

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> frontend = hap.frontend('frontend1_proc34')
          >>> frontend.maxconn
          >>> frontend.setmaxconn(50000)
          True
          >>> frontend.maxconn
          100000
        """
        if not isinstance(value, int):
            raise ValueError("Expected integer and got {}".format(type(value)))

        cmd = "set maxconn frontend {} {}".format(self.name, value)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    @property
    def name(self):
        """Return the name of the frontend.

        :rtype: ``string``
        """
        return self._name

    @property
    def process_nb(self):
        """Return a list of process number in which frontend is configured.

        :rtype: ``list``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> frontend = hap.frontend('frontend2_proc34')
          >>> frontend.process_nb
          [4, 3]
        """
        process_numbers = []
        for frontend in self._frontend_per_proc:
            process_numbers.append(frontend.process_nb)

        return process_numbers

    @property
    def requests(self):
        """Return the number of requests.

        :rtype: ``integer``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> frontend = hap.frontend('frontend2_proc34')
          >>> frontend.requests
          5
        """
        return self.metric('req_tot')

    def requests_per_process(self):
        """Return the number of requests for the frontend per process.

        :return: a list of tuples with 2 elements

          #. process number of HAProxy
          #. requests

        :rtype: ``list``

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> frontend = hap.frontend('frontend2_proc34')
          >>> frontend.requests_per_process()
          [(4, 2), (3, 3)]
        """
        results = cmd_across_all_procs(self._frontend_per_proc, 'metric',
                                       'req_tot')

        return results

    @should_die
    def shutdown(self):
        """Disable the frontend.

        .. warning::
           HAProxy removes from the running configuration a frontend, so
           further operations on the frontend will return an error.

        :rtype: ``bool``
        """
        cmd = "shutdown frontend {}".format(self.name)
        results = cmd_across_all_procs(self._frontend_per_proc, 'command', cmd)

        return check_command(results)

    def stats_per_process(self):
        """Return all stats of the frontend per process.

        :return: a list of tuples with 2 elements

          #. process number
          #. a dict with all stats

        :rtype: ``list``

        """
        results = cmd_across_all_procs(self._frontend_per_proc, 'stats')

        return results

    @property
    def status(self):
        """Return the status of the frontend.

        :rtype: ``string``
        :raise: :class:`IncosistentData` exception if status is different
          per process

        Usage::

          >>> from haproxyadmin import haproxy
          >>> hap = haproxy.HAProxy(socket_dir='/run/haproxy')
          >>> frontend = hap.frontend('frontend2_proc34')
          >>> frontend.status
          'OPEN'
        """
        results = cmd_across_all_procs(self._frontend_per_proc, 'metric',
                                       'status')

        return compare_values(results)
