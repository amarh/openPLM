#! /usr/bin/env sh

# usage: extrator.sh FILE

# this simple script extracts some metadata or data (as plain text) and
# prints them to stdout
# errors are silently passed

# TODO: remove noise ("nieXXX:")
/usr/lib/tracker/tracker-extract  -v 1 -f $1 2> /dev/null

