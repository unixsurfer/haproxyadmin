# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.internal.frontend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides a class, which is used within haproxyadmin for creating a
object to work with a frontend. This object is associated only with a single
HAProxy process.


"""


class _Frontend:
    """Class for interacting with a frontend in one HAProxy process.

    :param hap_process: a :class:`_HAProxyProcess` object.
    :param name: frontend name.
    :type name: ``string``
    :param iid: unique proxy id of the frontend.
    :type iid: ``integer``
    """
    def __init__(self, hap_process, name, iid):
        self.hap_process = hap_process
        self._name = name
        self.hap_process_nb = self.hap_process.process_nb
        self._iid = iid

    @property
    def name(self):
        """Return a string which is the name of the frontend"""
        return self._name

    @property
    def iid(self):
        """Return Proxy ID"""
        data = self.stats_data()
        self._iid = data.iid

        return self._iid

    @property
    def process_nb(self):
        return int(self.hap_process_nb)

    def stats_data(self):
        """Return stats data

        :rtype: ``utils.CSVLine`` object

        HAProxy assigns unique ids to each object during the startup.
        The id can change when configuration changes, objects order
        is reshuffled or additions/removals take place.
        In those cases the id we store at the instantiation of the object may
        reference to another object or even to non-existent object when
        configuration takes places afterwards.

        The technique we use is quite simple. When an object is created
        we store the name and the id. In order to detect if iid is changed,
        we simply send a request to fetch data only for the given iid and check
        if the current id points to an object of the same type
        (frontend, backend, server) which has the same name.
        """
        # Fetch data using the last known iid
        try:
            data = self.hap_process.frontends_stats(self._iid)[self.name]
        except KeyError:
            # A lookup on HAProxy with the current id doesn't return
            # an object with our name.
            # Most likely object got different id due to a reshuffle in conf.
            # Thus retrieve all objects to get latest data for the object.
            try:
                # This will basically request all object of the type
                data = self.hap_process.frontends_stats()[self.name]
            except KeyError:
                # The object has gone from running configuration!
                # This occurs when object was removed from configuration
                # and haproxy was reloaded or frontend was shutdowned.
                # We cant recover from this situation
                raise

        return data

    def stats(self):
        """Build dictionary for all statistics reported by HAProxy.

        :return: A dictionary with statistics
        :rtype: ``dict``
8. split internal to multiple files
        """
        data = self.stats_data()
        keys = data.heads
        values = data.parts

        return dict(zip(keys, values))

    def metric(self, name):
        """Return the value of a metric"""
        data = self.stats_data()

        return getattr(data, name)

    def command(self, cmd):
        """Run command to HAProxy

        :param cmd: a valid command to execute.
        :type cmd: ``string``
        :return: 1st line of the output.
        :rtype: ``string``
        """
        return self.hap_process.command(cmd)
