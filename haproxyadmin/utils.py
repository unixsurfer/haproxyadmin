# pylint: disable=superfluous-parens
#
"""
haproxyadmin.utils
~~~~~~~~~~~~~~~~~~

This module provides utility functions and classes that are used within
haproxyadmin.

"""

import socket
import os
import stat
from functools import wraps
import six
import re

from haproxyadmin.exceptions import (CommandFailed, MultipleCommandResults,
                                     IncosistentData)
from haproxyadmin.command_status import (ERROR_OUTPUT_STRINGS,
        SUCCESS_OUTPUT_STRINGS, SUCCESS_STRING_PORT, SUCCESS_STRING_ADDRESS)

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
    argument to the decorated function with the name ``die`` to control this
    behavior. When it is set to ``True``, which is the default value, it
    raises any exception raised by the decorated function. When it is set to
    ``False`` it returns ``True`` if decorated function run successfully or
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

def connected_socket(path, timeout):
    """Check if socket file is a valid HAProxy socket file.

    We send a 'show info' command to the socket, build a dictionary structure
    and check if 'Name' key is present in the dictionary to confirm that
    there is a HAProxy process connected to it.

    :param path: file name path
    :type path: ``string``
    :param timeout: timeout for the connection, in seconds
    :type timeout: ``float``
    :return: ``True`` is socket file is a valid HAProxy stats socket file False
      otherwise
    :rtype: ``bool``
    """
    try:
        unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        unix_socket.settimeout(timeout)
        unix_socket.connect(path)
        unix_socket.send(six.b('show info' + '\n'))
        file_handle = unix_socket.makefile()
    except (socket.timeout, OSError):
        return False
    else:
        try:
            data = file_handle.read().splitlines()
        except (socket.timeout, OSError):
            return False
        else:
            hap_info = info2dict(data)
    finally:
        unix_socket.close()

    try:
        return hap_info['Name'] in ['HAProxy', 'hapee-lb']
    except KeyError:
        return False


def cmd_across_all_procs(hap_objects, method, *arg, **kargs):
    """Return the result of a command executed in all HAProxy process.

    .. note::
        Objects must have a property with the name 'process_nb' which
        returns the HAProxy process number.

    :param hap_objects: a list of objects.
    :type hap_objects: ``list``
    :param method: a valid method for the objects.
    :return: list of 2-item tuple

      #. HAProxy process number
      #. what the method returned

    :rtype: ``list``
    """
    results = []
    for obj in hap_objects:
        results.append(
            (getattr(obj, 'process_nb'), getattr(obj, method)(*arg, **kargs))
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
    return len(set(iterator)) == 1


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

def check_command_addr_port(change_type, results):
    """Check if command to set port or address was successfully executed.

    Unfortunately, haproxy returns many different combinations of output when
    we change the address or the port of the server and trying to determine
    if address or port was successfully changed isn't that trivial.

    So, after we change address or port, we check if the same output is
    returned by all processes and we also check if a collection of specific
    strings are part of the output. This is a suboptimal solution, but I
    couldn't come up with something more elegant.

    :param change_type: either ``addr`` or ``port``
    :type change_type: ``string``
    :param results: a list of tuples with 2 elements.

          #. process number of HAProxy
          #. message returned by HAProxy
    :type results: ``list``
    :return: ``True`` if command was successfully executed otherwise ``False``.
    :rtype: ``bool``
    :raise: :class:`.MultipleCommandResults`, :class:`.CommandFailed` and
      :class:`ValueError`.
    """
    if change_type == 'addr':
        _match = SUCCESS_STRING_ADDRESS
    elif change_type == 'port':
        _match = SUCCESS_STRING_PORT
    else:
        raise ValueError('invalid value for change_type')

    if elements_of_list_same([msg[1] for msg in results]):
        msg = results[0][1]
        if re.match(_match, msg):
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
    if not metrics:
        return 0

    if name in METRICS_SUM:
        return sum(metrics)
    elif name in METRICS_AVG:
        return int(sum(metrics)/len(metrics))
    else:
        # This is to catch the case where the caller forgets to check if
        # metric name is a valide metric for HAProxy.
        raise ValueError("Unknown type of calculation for {}".format(name))

def isint(value):
    """Check if input can be converted to an integer

    :param value: value to check
    :type value: a ``string`` or ``int``
    :return: ``True`` if value can be converted to an integer
    :rtype: ``bool``
    :raise: :class:`ValueError` when value can't be converted to an integer
    """
    try:
        int(value)
        return True
    except ValueError:
        return False

def converter(value):
    """Tries to convert input value to an integer.

    If input can be safely converted to number it returns an ``int`` type.
    If input is a valid string but not an empty one it returns that.
    In all other cases we return None, including the ones which an
    ``TypeError`` exception is raised by ``int()``.
    For floating point numbers, it truncates towards zero.

    Why are we doing this?
    HAProxy may return for a metric either a number or zero or string or an
    empty string.

    It is up to the caller to correctly use the returned value. If the returned
    value is passed to a function which does math operations the caller has to
    filtered out possible ``None`` values.

    :param value: a value to convert to int.
    :type value: ``string``
    :rtype: ``integer or ``string`` or ``None`` if value can't be converted
            to ``int`` or to ``string``.

    Usage::

      >>> from haproxyadmin import utils
      >>> utils.converter('0')
      0
      >>> utils.converter('13.5')
      13
      >>> utils.converter('13.5f')
      '13.5f'
      >>> utils.converter('')
      >>> utils.converter(' ')
      >>> utils.converter('UP')
      'UP'
      >>> utils.converter('UP 1/2')
      'UP 1/2'
      >>>
    """
    try:
        return int(float(value))
    except ValueError:
        # if it isn't an empty string return it otherwise return None
        return value.strip() or None
    except TypeError:
        # This is to catch the case where input value is a data structure or
        # object. It is very unlikely someone to pass those, but you never know.
        return None


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
    """Build a dictionary structure from the output of 'show info' command.

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
