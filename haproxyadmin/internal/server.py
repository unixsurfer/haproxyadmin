# -*- coding: utf-8 -*-
#
# pylint: disable=superfluous-parens
#
"""
haproxyadmin.internal.server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides a class, which is used within haproxyadmin for creating a
object to work with a server. This object is associated only with a single
HAProxy process.

"""

class _Server:
    """Class for interacting with a server of a backend in one HAProxy.

    :param backend: a _Backend object in which server is part of.
    :param name: server name.
    :type name: ``string``
    :param sid: server id (unique inside a proxy).
    :type sid: ``string``
    """
    def __init__(self, backend, name, sid):
        self.backend = backend
        self._name = name
        self.process_nb = self.backend.process_nb
        self._sid = sid

    @property
    def name(self):
        """Return the name of the backend server."""
        return self._name

    @property
    def sid(self):
        """Return server id"""
        data = self.stats_data()
        self._sid = data.sid

        return self._sid

    def stats_data(self):
        """Return stats data

        Check documentation of ``stats_data`` method in :class:`_Frontend`.

        :rtype: ``utils.CSVLine`` object
        """
        # Fetch data using the last known sid
        try:
            data = self.backend.hap_process.servers_stats(
                self.backend.name, self.backend.iid, self._sid)[self.name]
        except KeyError:
            # A lookup on HAProxy with the current id doesn't return
            # an object with our name.
            # Most likely object got different id due to a reshuffle in conf.
            # Thus retrieve all objects to get latest data for the object.
            try:
                data = self.backend.hap_process.servers_stats(
                    self.backend.name)[self.name]
            except KeyError:
                # The object has gone from running configuration!
                # This occurs when object was removed from configuration
                # and haproxy was reloaded.We cant recover from this situation.
                raise

        return data

    def metric(self, name):
        data = self.stats_data()

        return getattr(data, name)

    def stats(self):
        """Build dictionary for all statistics reported by HAProxy.

        :return: A dictionary with statistics
        :rtype: ``dict``
        """
        data = self.stats_data()
        keys = data.heads
        values = data.parts

        return dict(zip(keys, values))

    def command(self, cmd):
        return self.backend.hap_process.command(cmd)
