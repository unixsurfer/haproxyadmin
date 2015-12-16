# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.backend
~~~~~~~~~~~~~~~~~~~~

This module provides the :class:`Backend <.Backend>` class which allows to
run operation for a backend.

"""
from haproxyadmin.utils import (calculate, cmd_across_all_procs,
                                compare_values, converter)
from haproxyadmin.server import Server


BACKEND_METRICS = [
    'act',
    'bck',
    'bin',
    'bout',
    'chkdown',
    'cli_abrt',
    'comp_byp',
    'comp_in',
    'comp_out',
    'comp_rsp',
    'ctime',
    'downtime',
    'dreq',
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
    'ttime',
    'weight',
    'wredis',
    'wretr',
]


class Backend(object):
    """Build a user-created :class:`Backend` for a single backend.

    :param backend_per_proc: list of :class:`._Backend` objects.
    :type backend_per_proc: ``list``
    :rtype: a :class:`Backend`.
    """

    def __init__(self, backend_per_proc):
        self._backend_per_proc = backend_per_proc
        self._name = self._backend_per_proc[0].name

    # built-in comparison operator is adjusted
    def __eq__(self, other):
        if isinstance(other, Backend):
            return (self.name == other.name)
        elif isinstance(other, str):
            return (self.name == other)
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    @property
    def iid(self):
        """Return the unique proxy ID of the backend.

        .. note::
            Because proxy ID is the same across all processes,
            we return the proxy ID from the 1st process.

        :rtype: ``int``
        """
        return int(self._backend_per_proc[0].iid)

    def servers(self, name=None):
        """Return Server object for each server.

        :param name: (optional) servername to look for. Defaults to None.
        :type name: string
        :return: A list of :class:`Server <Server>` objects
        :rtype: list
        """
        return_list = []

        # store _Server objects for each server as it is reported by each
        # process.
        # key: name of the server
        # value: a list of _Server object
        servers_across_hap_processes = {}

        # Get a list of servers (_Server objects) per process
        for backend in self._backend_per_proc:
            for server in backend.servers(name):
                if server.name not in servers_across_hap_processes:
                    servers_across_hap_processes[server.name] = []
                servers_across_hap_processes[server.name].append(server)

        # For each server build a Server object
        for server_per_proc in servers_across_hap_processes.values():
            return_list.append(Server(server_per_proc, self.name))

        return return_list

    def server(self, name):
        """Return a Server object

        :param name: Name of the server
        :type name: string
        :return: :class:`Server <Server>` object
        :rtype: haproxyadmin.Server
        """
        server = self.servers(name)
        if len(server) == 1:
            return server[0]
        elif len(server) == 0:
            raise ValueError("Could not find server")
        else:
            raise ValueError("Found more than one server, this is a bug!")

    def metric(self, name):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        utils.METRICS_SUM and utils.METRICS_AVG.

        :param name: Name of the metric, any of BACKEND_METRICS
        :type name: ``string``
        :return: Value of the metric after the appropriate calculation
          has been performed.
        :rtype: number, either ``integer`` or ``float``.
        :raise: ValueError when a given metric is not found.
        """
        metrics = []
        if name not in BACKEND_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._backend_per_proc]
        metrics[:] = (converter(x) for x in metrics)
        metrics[:] = (x for x in metrics if x is not None)

        return calculate(name, metrics)

    @property
    def name(self):
        """Return the name of the backend.

        :rtype: string
        """
        return self._name

    @property
    def process_nb(self):
        """Return a list of process number in which backend is configured.

        :rtype: list
        """
        process_numbers = []
        for backend in self._backend_per_proc:
            process_numbers.append(backend.process_nb)

        return process_numbers

    @property
    def requests(self):
        """Return the number of requests.

        :rtype: integer
        """
        return self.metric('stot')

    def requests_per_process(self):
        """Return the number of requests for the backend per process.

        :return: a list of tuples with 2 elements

          #. process number of HAProxy
          #. requests

        :rtype: ``list``

        """
        results = cmd_across_all_procs(self._backend_per_proc, 'metric', 'stot')

        return results

    def stats_per_process(self):
        """Return all stats of the backend per process.

        :return: a list of tuples with 2 elements

          #. process number
          #. a dict with all stats

        :rtype: ``list``

        """
        values = cmd_across_all_procs(self._backend_per_proc, 'stats')

        return values

    @property
    def status(self):
        """Return the status of the backend.

        :rtype: ``string``
        :raise: :class:`IncosistentData` exception if status is different
          per process.

        """
        results = cmd_across_all_procs(self._backend_per_proc, 'metric', 'status')

        return compare_values(results)
