# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.internal.backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides a class, which is used within haproxyadmin for creating a
object to work with a backend. This object is associated only with a single
HAProxy process.

"""
from haproxyadmin.internal.server import _Server

class _Backend:
    """Class for interacting with a backend in one HAProxy process.

    :param hap_process: a :class::`_HAProxyProcess` object.
    :param name: backend name.
    :type name: ``string``
    :param iid: unique proxy id of the backend.
    :type iid: ``integer``
    """
    def __init__(self, hap_process, name, iid):
        self.hap_process = hap_process
        self._name = name
        self.hap_process_nb = self.hap_process.process_nb
        self._iid = iid

    @property
    def name(self):
        """Return a string which is the name of the backend"""
        return self._name

    @property
    def iid(self):
        """Return Proxy ID"""
        data = self.stats_data()
        self._iid = data.iid

        return self._iid

    @property
    def process_nb(self):
        """Return the process number of the haproxy process

        :rtype: ``int``
        """
        return int(self.hap_process_nb)

    def stats_data(self):
        """Return stats data

        Check documentation of ``stats_data`` method in :class:`_Frontend`.

        :rtype: ``utils.CSVLine`` object
        """
        # Fetch data using the last known iid
        try:
            data = self.hap_process.backends_stats(self._iid)[self.name]
        except KeyError:
            # A lookup on HAProxy with the current id doesn't return
            # an object with our name.
            # Most likely object got different id due to a reshuffle in conf.
            # Thus retrieve all objects to get latest data for the object.
            try:
                data = self.hap_process.backends_stats()[self.name]
            except KeyError:
                # The object has gone from running configuration!
                # We cant recover from this situation.
                raise

        return data['stats']

    def stats(self):
        """Build dictionary for all statistics reported by HAProxy.

        :return: A dictionary with statistics
        :rtype: ``dict``
        """
        data = self.stats_data()
        keys = data.heads
        values = data.parts

        return dict(zip(keys, values))

    def metric(self, name):
        data = self.stats_data()

        return getattr(data, name)

    def command(self, cmd):
        """Send command to HAProxy

        :param cmd: command to send
        :type cmd: ``string``
        :return: the output of the command
        :rtype: ``string``
        """
        return self.hap_process.command(cmd)

    def servers(self, name=None):
        """Return a list of _Server objects for each server of the backend.

        :param name: (optional): server name to lookup, defaults to None.
        :type name: ``string``
        """
        servers = []
        return_list = []

        servers = self.hap_process.servers_stats(self.name, self.iid)
        if name is not None:
            if name in servers:
                return_list.append(_Server(self,
                                           name,
                                           servers[name].sid))
            else:
                return []
        else:
            for _name in servers:
                return_list.append(_Server(self,
                                           _name,
                                           servers[_name].sid))

        return return_list
