#!/usr/bin/python
from django.core.management import execute_manager

try:
    import settings # Assumed to be in the same directory.
except ImportError as er:
    import sys
    # print 'er' in case of a missing module dependence
    # reported by Jason Morgan
    sys.stderr.write(str(er))
    sys.stderr.write("\nError: Can't find the file 'settings.py' in the directory\n")
    sys.exit(1)

import SocketServer
import django.core.servers.basehttp
django.core.servers.basehttp.WSGIServer = \
    type('WSGIServer',
         (SocketServer.ThreadingMixIn,
          django.core.servers.basehttp.WSGIServer,
          object),
         {})

if __name__ == "__main__":
    execute_manager(settings)
