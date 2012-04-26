#! /usr/bin/env python
import re
import sys
from random import choice

MAIN_SETTINGS_FILE = "settings.py"
if __name__ == "__main__":
    if len(sys.argv) == 2:
        main_settings_file = sys.argv[1]
    else:
        main_settings_file = MAIN_SETTINGS_FILE
    with open(main_settings_file, 'r+') as fp:
        settings_contents = fp.read()
        fp.seek(0)
        secret_key = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
        settings_contents = re.sub(r"(?<=SECRET_KEY = ')[^']+'", secret_key + "'", settings_contents)
        fp.write(settings_contents)
        fp.close()
