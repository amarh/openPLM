#!/usr/bin/env python
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "openPLM.settings")

try:
    import settings # Assumed to be in the same directory.
except ImportError as er:
    # print 'er' in case of a missing module dependence
    # reported by Jason Morgan
    sys.stderr.write(str(er))
    sys.stderr.write("\nError: Can't find the file 'settings.py' in the directory\n")
    sys.exit(1)
if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
