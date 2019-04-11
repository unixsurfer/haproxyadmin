# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
haproxyadmin.command_status.py
~~~~~~~~~~~~~~~~~~~

This module categorizes the output returned by various commands

"""
# CLI doesn't return a message if operation is successfully executed.
# But, versions prior 1.5.10 was returning 'Done.' message only for ACL/MAPs
# operations. 73f1d8f447087 commit in haproxy-1.5 makes the output consistent
# by removing 'Done.' message.
SUCCESS_OUTPUT_STRINGS = [
    'Done.',
    ''
]

ERROR_OUTPUT_STRINGS = [
    "'add acl' expects two parameters: ACL identifier and pattern.",
    "'add map' expects three parameters: map identifier, key and value.",
    "'add' only supports 'map'.",
    "A frontend name is expected.",
    "agent checks are not enabled on this server.",
    "Agent was not configured on this server, cannot enable.",
    "cannot change health on a tracking server.",
    "content-based lookup is only supported with the \"show\" and \"clear\" actions",
    "\"data.<type>\" followed by a value expected",
    "Data type not stored in this table",
    "'del' only supports 'map' or 'acl'.",
    "'disable' only supports 'agent', 'frontend', 'health', and 'server'.",
    "'enable' only supports 'agent', 'frontend', 'health', and 'server'.",
    "Entry currently in use, cannot remove",
    "Expects a maximum input byte rate in kB/s.",
    "Expects an integer value.",
    "Failed to pause frontend, check logs for precise cause.",
    "Failed to resume frontend, check logs for precise cause (port conflict?).",
    "Frontend is already disabled.",
    "Frontend is already enabled.",
    "Frontend was already shut down.",
    "Frontend was previously shut down, cannot disable.",
    "Frontend was previously shut down, cannot enable.",
    "HAProxy was compiled against a version of OpenSSL that doesn't support OCSP stapling.",
    "Health checks are not configured on this server, cannot enable.",
    "Integer value expected.",
    "Invalid key",
    "Invalid timeout value.",
    "Key not found.",
    "Key value expected",
    "Malformed identifier. Please use #<id> or <file>.",
    "Missing ACL identifier.",
    "Missing ACL identifier and/or key.",
    "Missing map identifier.",
    "Missing map identifier and/or key.",
    "No such backend.",
    "No such frontend.",
    "No such server.",
    "No such session (use 'show sess').",
    "No such table",
    "OCSP Response updated!",
    "Optional argument only supports \"data.<store_data_type>\" <operator> <value> and key <key>",
    "Out of memory error.",
    "Proxy is disabled.",
    "Removing keys from ip tables of type other than ip, ipv6, string and integer is not supported",
    "Require and operator among \"eq\", \"ne\", \"le\", \"ge\", \"lt\", \"gt\"",
    "Require a valid integer value to compare against",
    "Require a valid integer value to store",
    "Require 'backend/server'.",
    "Required arguments: <table> \"data.<store_data_type>\" <operator> <value> or <table> key <key>",
    "Session pointer expected (use 'show sess').",
    "'set map' expects three parameters: map identifier, key and value.",
    "'set maxconn' only supports 'frontend' and 'global'.",
    "'set rate-limit connections' only supports 'global'.",
    "'set rate-limit http-compression' only supports 'global'.",
    "'set rate-limit sessions' only supports 'global'.",
    "'set rate-limit ssl-sessions' only supports 'global'.",
    "'set rate-limit' supports 'connections', 'sessions', 'ssl-sessions', and 'http-compression'.",
    "'set server <srv> agent' expects 'up' or 'down'.",
    "'set server <srv> health' expects 'up', 'stopping', or 'down'.",
    "'set server <srv>' only supports 'agent', 'health', 'state', 'weight' add 'addr'.",
    "'set server <srv> state' expects 'ready', 'drain' and 'maint'.",
    "'set ssl ocsp-response' expects response in base64 encoding.",
    "'set ssl ocsp-response' received invalid base64 encoded response.",
    "'set ssl' only supports 'ocsp-response'.",
    "'set timeout' only supports 'cli'.",
    "Showing keys from tables of type other than ip, ipv6, string and integer is not supported",
    "'shutdown' only supports 'frontend', 'session' and 'sessions'.",
    "'shutdown sessions' only supports 'server'.",
    "This ACL is shared with a map containing samples. ",
    "This command expects two parameters: ACL identifier and key.",
    "This command expects two parameters: map identifier and key.",
    "Unable to allocate a new entry",
    "Unknown ACL identifier. Please use #<id> or <file>.",
    "Unknown action",
    "Unknown data type",
    "Unknown map identifier. Please use #<id> or <file>.",
    "Unknown command. Please enter one of the following commands only :",
    "Value out of range.",
    "Missing resolver section identifier.",
    "Can't find resolvers section.",
    "Can't find backend.",
]

SUCCESS_STRING_ADDRESS = "IP changed from|no need to change the addr"
SUCCESS_STRING_PORT = ("no need to change the addr, port changed from|no need "
                       "to change the addr, no need to change the port"
                      )
