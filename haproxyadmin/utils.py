# pylint: disable=superfluous-parens
#
"""
haproxyadmin.utils
~~~~~~~~~~~~~~~~~~

This module provides utility functions and classes that are used within
haproxyadmin.

"""

import socket
import six
from six.moves import filter
import os
import stat
from functools import wraps
from .exceptions import (CommandFailed, MultipleCommandResults,
                         IncosistentData, SocketPermissionError,
                         SocketConnectionError, SocketApplicationError)
from .command_status import ERROR_OUTPUT_STRINGS, SUCCESS_OUTPUT_STRINGS

METRICS_SUM = [
    'CompressBpsIn',
    'CompressBpsOut',
    'CompressBpsRateLim',
    'ConnRate',
    'ConnRateLimit',
    'CumConns',
    'CumReq',
    'CumSslConns',
    'CurrConns',
    'CurrSslConns',
    'Hard_maxconn',
    'Idle_pct',
    'MaxConnRate',
    'MaxSessRate',
    'MaxSslConns',
    'MaxSslRate',
    'MaxZlibMemUsage',
    'Maxconn',
    'Maxpipes',
    'Maxsock',
    'Memmax_MB',
    'PipesFree',
    'PipesUsed',
    'Process_num',
    'Run_queue',
    'SessRate',
    'SessRateLimit',
    'SslBackendKeyRate',
    'SslBackendMaxKeyRate',
    'SslCacheLookups',
    'SslCacheMisses',
    'SslFrontendKeyRate',
    'SslFrontendMaxKeyRate',
    'SslFrontendSessionReuse_pct',
    'SslRate',
    'SslRateLimit',
    'Tasks',
    'Ulimit-n',
    'ZlibMemUsage',
    'bin',
    'bout',
    'chkdown',
    'chkfail',
    'comp_byp',
    'comp_in',
    'comp_out',
    'comp_rsp',
    'cli_abrt',
    'dreq',
    'dresp',
    'ereq',
    'eresp',
    'econ',
    'hrsp_1xx',
    'hrsp_2xx',
    'hrsp_3xx',
    'hrsp_4xx',
    'hrsp_5xx',
    'hrsp_other',
    'lbtot',
    'qcur',
    'qmax',
    'rate',
    'rate_lim',
    'rate_max',
    'req_rate',
    'req_rate_max',
    'req_tot',
    'scur',
    'slim',
    'srv_abrt',
    'smax',
    'stot',
    'wretr',
    'wredis',
]

METRICS_AVG = [
    'act',
    'bck',
    'check_duration',
    'ctime',
    'downtime',
    'lastchg',
    'lastsess',
    'qlimit',
    'qtime',
    'rtime',
    'throttle',
    'ttime',
    'weight',
]


def should_die(old_implementation):
    """Build a decorator to control exceptions.

    When a function raises an exception in some cases we don't care for the
    reason but only if the function run successfully or not. We add an extra
    argument to the decorating function with the name ``die`` to control this
    behavior. When it is set to ``True``, which is the default value, it
    raises any exception raised by the decorating function. When it is set to
    ``False`` it returns ``True`` if decorating function run successfully or
    ``False`` if an exception was raised.
    """
    @wraps(old_implementation)
    def new_implementation(*args, **kwargs):
        try:
            die = kwargs['die']
            del(kwargs['die'])
        except KeyError:
            die = True

        try:
            rv = old_implementation(*args, **kwargs)
            return rv
        except Exception as error:
            if die:
                raise error
            else:
                return False

    return new_implementation


def is_unix_socket(path):
    """Return ``True`` if path is a valid UNIX socket otherwise False.

    :param path: file name path
    :type path: ``string``
    :rtype: ``bool``
    """
    mode = os.stat(path).st_mode

    return stat.S_ISSOCK(mode)


def connected_socket(path):
    """Check if socket file is a valid HAProxy socket file.

    We send a 'show info' command to the socket, build a dictionary structure
    and check if 'Name' key is present in the dictionary to confirm that
    there is a HAProxy process connected to it.

    :param path: file name path
    :type path: ``string``
    :rtype: ``bool``
    :raise: :class:`.SocketPermissionError`, :class:`.SocketConnectionError`
      and :class:`.SocketApplicationError`
    """
    try:
        unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        unix_socket.settimeout(0.1)
        unix_socket.connect(path)
        unix_socket.send(six.b('show info' + '\n'))
        file_handle = unix_socket.makefile()
        data = file_handle.read().splitlines()
        hap_info = info2dict(data)
    except ConnectionRefusedError:
        raise SocketConnectionError(path)
    except PermissionError:
        raise SocketPermissionError(path)

    try:
        if hap_info['Name'] == 'HAProxy':
            return True
        else:
            raise SocketApplicationError(path)
    except KeyError:
        raise SocketApplicationError(path)


def cmd_across_all_procs(hap_objects, method, *arg):
    """Return the result of a command executed in all HAProxy process.

    .. note::
        Objects must have a property with the name 'process_nb' which
        returns the HAProxy process number.

    :param hap_objects: a list of objects.
    :type hap_objects: ``list``
    :param method: a valid method for the objects.
    :param arg: (optional) argument on the method
    :type arg: whatever is acceptable for the method
    :return: list of 2-item tuple

      #. HAProxy process number
      #. what the method returned

    :rtype: ``list``
    """
    results = []
    for obj in hap_objects:
        results.append(
            (getattr(obj, 'process_nb'), getattr(obj, method)(*arg))
        )

    return results


def elements_of_list_same(iterator):
    """Check is all elements of an iterator are equal.

    :param iterator: a iterator
    :type iterator: ``list``
    :rtype: ``bool``

    Usage::

      >>> from haproxyadmin import utils
      >>> iterator = ['OK', 'ok']
      >>> utils.elements_of_list_same(iterator)
      False
      >>> iterator = ['OK', 'OK']
      >>> utils.elements_of_list_same(iterator)
      True
      >>> iterator = [22, 22, 22]
      >>> utils.elements_of_list_same(iterator)
      True
      >>> iterator = [22, 22, 222]
      >>> utils.elements_of_list_same(iterator)
      False
    """
    length = len(set(iterator))
    if length == 1:
        return True
    else:
        return False


def compare_values(values):
    """Run an intersection test across values returned by processes.

    It is possible that not all processes return the same value for certain
    keys(status, weight etc) due to various reasons. We must detect these cases
    and either return the value which is the same across all processes or
    raise :class:`<IncosistentData>`.

    :param values: a list of tuples with 2 elements.

        #. process number of HAProxy process returned the data
        #. value returned by HAProxy process.

    :type values: ``list``
    :return: value
    :rtype: ``string``
    :raise: :class:`.IncosistentData`.
    """
    if elements_of_list_same([msg[1] for msg in values]):
        return values[0][1]
    else:
        raise IncosistentData(values)


def check_output(output):
    """Check if output contains any error.

    Several commands return output which we need to return back to the caller.
    But, before we return anything back we want to perform a sanity check on
    on the output in order to catch wrong input as it is impossible to
    perform any sanitization on values/patterns which are passed as input to
    the command.

    :param output: output of the command.
    :type output: ``list``
    :return: ``True`` if no errors found in output otherwise ``False``.
    :rtype: ``bool``
    """
    # We only care about the 1st line as that one contains possible error
    # message
    first_line = output[0]
    if first_line in ERROR_OUTPUT_STRINGS:
        return False
    else:
        return True


def check_command(results):
    """Check if command was successfully executed.

    After a command is executed. We care about the following cases:

        * The same output is returned by all processes
        * If output matches to a list of outputs which indicate that
          command was valid

    :param results: a list of tuples with 2 elements.

          #. process number of HAProxy
          #. message returned by HAProxy

    :type results: ``list``
    :return: ``True`` if command was successfully executed otherwise ``False``.
    :rtype: ``bool``
    :raise: :class:`.MultipleCommandResults` when output differers.
    """
    if elements_of_list_same([msg[1] for msg in results]):
        msg = results[0][1]
        if msg in SUCCESS_OUTPUT_STRINGS:
            return True
        else:
            raise CommandFailed(msg)
    else:
        raise MultipleCommandResults(results)


def calculate(name, metrics):
    """Perform the appropriate calculation across a list of metrics.

    :param name: name of the metric.
    :type name: ``string``
    :param metrics: a list of metrics. Elements need to be either ``int``
      or ``float`` type number.
    :type metrics: ``list``
    :return: either the sum or the average of metrics.
    :rtype: ``integer``
    :raise: :class:`ValueError` when matric name has unknown type of
      calculation.
    """
    # Remove empty values, for some metrics HAProxy returns '' instead of 0
    filtered = filter(None, metrics)
    if name in METRICS_SUM:
        return round(sum(filtered))
    elif name in METRICS_AVG:
        return round(sum(filtered) / len(metrics))
    else:
        raise ValueError("Unknown type of calculation for {}".format(name))


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def isint(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def converter(value):
    """Convert a number or string to an integer

    For floating point numbers, this truncates towards zero.

    :param value: a value to convert to int.
    :type value: ``string``
    :rtype: ``integer or ``string`` if value can't be converted to int.

    Usage::

      >>> from haproxyadmin import utils
      >>> utils.converter('5.0')
      5
      >>> utils.converter('5.0j')
      '5.0j'
      >>> utils.converter('5.0')
      5
      >>> utils.converter(5.0)
      5
      >>> utils.converter(5)
      5
    """
    if isint(value):
        return int(value)
    elif isfloat(value):
        return int(float(value))
    else:
        return value


class CSVLine(object):
    """An object that holds field/value of a CSV line.

    The field name becomes the attribute of the class.
    Needs the header line of CSV during instantiation.

    :param parts: A list with field values
    :type parts: list

    Usage::

      >>> from haproxyadmin import utils
      >>> heads = ['pxname', 'type', 'lbtol']
      >>> parts = ['foor', 'backend', '444']
      >>> utils.CSVLine.heads = heads
      >>> csvobj = utils.CSVLine(parts)
      >>> csvobj.pxname
      'foor'
      >>> csvobj.type
      'backend'
      >>> csvobj.lbtol
      '444'
      >>> csvobj.bar
      Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/.../haproxyadmin/haproxyadmin/utils.py", line 341, in __getattr__
          _index = self.heads.index(attr)
      ValueError: 'bar' is not in list
    """
    # This holds the field names of the CSV
    heads = []

    def __init__(self, parts):
        self.parts = parts

    def __getattr__(self, attr):
        _index = self.heads.index(attr)
        setattr(self, attr, self.parts[_index])

        return self.parts[_index]


def info2dict(raw_info):
    """Build a dictionary structure.

    :param raw_info: data returned by 'show info' UNIX socket command
    :type raw_info: ``list``
    :return: A dictionary with the following keys/values(examples)

    .. code-block:: python

       {
           Name: HAProxy
           Version: 1.4.24
           Release_date: 2013/06/17
           Nbproc: 1
           Process_num: 1
           Pid: 1155
           Uptime: 5d 4h42m16s
           Uptime_sec: 448936
           Memmax_MB: 0
           Ulimit-n: 131902
           Maxsock: 131902
           Maxconn: 65536
           Maxpipes: 0
           CurrConns: 1
           PipesUsed: 0
           PipesFree: 0
           Tasks: 819
           Run_queue: 1
           node: node1
           description:
       }

    :rtype: ``dict``
    """
    info = {}
    for line in raw_info:
        line = line.lstrip()
        if ': ' in line:
            key, value = line.split(': ', 1)
            info[key] = value

    return info


def stat2dict(csv_data):
    """Build a nested dictionary structure.

    :param csv_data: data returned by 'show stat' command in a CSV format.
    :type csv_data: ``list``
    :return: a nested dictionary with all counters/settings found in the input.
      Following is a sample of the structure::

        {
            'backends': {
                'acq-misc': {
                                'stats': { _CSVLine object },
                                'servers': {
                                    'acqrdb-01': { _CSVLine object },
                                    'acqrdb-02': { _CSVLine object },
                                    ...
                                    }
                            },
                ...
                },
            'frontends': {
                'acq-misc': { _CSVLine object },
                ...
                },
            ...
        }

    :rtype: ``dict``
    """
    heads = []
    dicts = {
        'backends': {},
        'frontends': {}
    }

    # get the header line
    headers = csv_data.pop(0)
    # make a shiny list of heads
    heads = headers[2:].strip().split(',')
    # set for all _CSVLine object the header fields
    CSVLine.heads = heads

    # We need to parse the following
    # haproxy,FRONTEND,,,...
    # haproxy,BACKEND,0,0,0...
    # test,FRONTEND,,,0,0,10...
    # dummy,BACKEND,0,0,0,0,1..
    # app_com,FRONTEND,,,0...
    # app_com,appfe-103.foo.com,0,...
    # app_com,BACKEND,0,0,...
    # monapp_com,FRONTEND,,,....
    # monapp_com,monappfe-102.foo.com,0...
    # monapp_com,BACKEND,0,0...
    # app_api_com,FRONTEND,,,...
    # app_api_com,appfe-105.foo.com,0...
    # app_api_com,appfe-106.foo.com,0...
    # app_api_com,BACKEND,0,0,0,0,100000,0,0,0,0,0,,0,0,...

    # A line which holds frontend definition:
    #     <frontent_name>,FRONTEND,....
    # A line holds server definition:
    #     <backend_name>,<servername>,....
    # A line which holds backend definition:
    #     <backend_name>,BACKEND,....
    # NOTE: we can have a single line for a backend definition without any
    # lines for servers associated with for that backend
    for line in csv_data:
        line = line.strip()
        if line:
            # make list of parts
            parts = line.split(',')
            # each line is a distinct object
            csvline = CSVLine(parts)
            # parts[0] => pxname field, backend or frontend name
            # parts[1] => svname field, servername or BACKEND or FRONTEND
            if parts[1] == 'FRONTEND':
                # This is a frontend line.
                # Frontend definitions aren't spread across multiple lines.
                dicts['frontends'][parts[0]] = csvline
            elif (parts[1] == 'BACKEND' and parts[0] not in dicts['backends']):
                # I see this backend information for 1st time.
                dicts['backends'][parts[0]] = {}
                dicts['backends'][parts[0]]['servers'] = {}
                dicts['backends'][parts[0]]['stats'] = csvline
            else:
                if parts[0] not in dicts['backends']:
                    # This line holds server information for a backend I haven't
                    # seen before, thus create the backend structure and store
                    # server details.
                    dicts['backends'][parts[0]] = {}
                    dicts['backends'][parts[0]]['servers'] = {}
                if parts[1] == 'BACKEND':
                    dicts['backends'][parts[0]]['stats'] = csvline
                else:
                    dicts['backends'][parts[0]]['servers'][parts[1]] = csvline

    return dicts
