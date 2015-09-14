TODO
====

#. Add support for sending commands to stats socket

#. Add support for TLS ticket operations

#. Add support for OCSP stapling

#. Add support for changing server's IP

#. Add support for DNS resolvers

#. Add support for dumping sessions

#. make internal._HAProxyProcess.send_command() to return file type object as it will avoid to run through the list 2 times.
We wont do any sanity checking on the input, we will just pass it to
stats socket and return back when sockets returns to us

#. Test against hapee, haproxy-1.6dev4

#. Investigate the use of __slots__ in utils.CSVLine as it could speed up
  the library when we create 100K objects
