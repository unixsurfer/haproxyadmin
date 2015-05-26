# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.pool
~~~~~~~~~~~~~~~~~

This module provides the :class:`Pool <.Pool>` class which allows to
run operation for a pool.

"""
from .utils import (calculate, cmd_across_all_procs, compare_values)
from .poolmember import PoolMember


class Pool(object):
    """A container for a pool across several HAProxy processes."""
    POOL_METRICS = [
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
        'status',
        'stot',
        'ttime',
        'weight',
        'wredis',
        'wretr',
    ]

    def __init__(self, pool_per_proc):
        self._pool_per_proc = pool_per_proc
        self._name = self._pool_per_proc[0].name

    # built-in comparison operator is adjusted
    def __eq__(self, other):
        if isinstance(other, Pool):
            return (self.name == other.name)
        elif isinstance(other, str):
            return (self.name == other)
        else:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    def members(self, name=None):
        """Return PoolMember object for each member.

        :param name: (optional) Membername to look for. Defaults to None.
        :type name: string
        :return: A list of :class:`PoolMember <PoolMember>` objects
        :rtype: list
        """
        return_list = []

        # store _PoolMember objects for each member as it is reported by each
        # process.
        # key: name of the member
        # value: a list of _PoolMember object
        members_across_hap_processes = {}

        # Get a list of members (_PoolMember objects) per process
        for pool in self._pool_per_proc:
            for member in pool.members(name):
                if member.name not in members_across_hap_processes:
                    members_across_hap_processes[member.name] = []
                members_across_hap_processes[member.name].append(member)

        # For each member build a PoolMember object
        for member_per_proc in members_across_hap_processes.values():
            return_list.append(PoolMember(member_per_proc, self.name))

        return return_list

    def member(self, name):
        """Return a PoolMember object

        :param name: Name of the member
        :type name: string
        :return: :class:`PoolMember <PoolMember>` object
        :rtype: haproxyadmin.PoolMember
        """
        member = self.members(name)
        if len(member) == 1:
            return member[0]
        elif len(member) == 0:
            raise ValueError("Could not find member")
        else:
            raise ValueError("Found more than one member, this is a bug!")

    def metric(self, name):
        """Return the value of a metric.

        Performs a calculation on the metric across all HAProxy processes.
        The type of calculation is either sum or avg and defined in
        utils.METRICS_SUM and utils.METRICS_AVG.

        :param name: Name of the metric, any of POOL_METRICS
        :type name: ``string``
        :return: Value of the metric after the appropriate calculation
          has been performed.
        :rtype: number, either ``integer`` or ``float``.
        :raise: ValueError when a given metric is not found.
        """
        metrics = []
        if name not in Pool.POOL_METRICS:
            raise ValueError("{} is not valid metric".format(name))

        metrics = [x.metric(name) for x in self._pool_per_proc]

        return calculate(name, metrics)

    @property
    def name(self):
        """Return the name of the pool.

        :rtype: string
        """
        return self._name

    @property
    def process_nb(self):
        """Return a list of process number in which pool is configured.

        :rtype: list
        """
        process_numbers = []
        for pool in self._pool_per_proc:
            process_numbers.append(pool.process_nb)

        return process_numbers

    @property
    def requests(self):
        """Return the number of requests.

        :rtype: integer
        """
        return self.metric('lbtot')

    def requests_per_process(self):
        """Return the number of requests for the pool per process.

        :return: a list of tuples with 2 elements

          #. process number of HAProxy
          #. requests

        :rtype: ``list``

        """
        results = cmd_across_all_procs(self._pool_per_proc, 'metric', 'lbtot')

        return results

    def stats_per_process(self):
        """Return all stats of the pool per process.

        :return: a list of tuples with 2 elements

          #. process number
          #. a dict with all stats

        :rtype: ``list``

        """
        values = cmd_across_all_procs(self._pool_per_proc, 'stats')

        return values

    @property
    def status(self):
        """Return the status of the pool.

        :rtype: ``string``
        :raise: :class:`IncosistentData` exception if status is different
          per process.

        """
        results = cmd_across_all_procs(self._pool_per_proc, 'metric', 'status')

        return compare_values(results)
