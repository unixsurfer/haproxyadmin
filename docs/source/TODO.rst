TODO
====

#. Add support for enabling/disabling health/agent checks

#. TLS ticket operations

#. Add support for TLS ticket operations

#. Add support for OCSP stapling

#. Add support for DNS resolvers

#. Add support for dumping sessions

#. make internal._HAProxyProcess.send_command() to return file type object as it will avoid to run through the list 2 times.

#. Investigate the use of __slots__ in utils.CSVLine as it could speed up the library when we create 100K objects
