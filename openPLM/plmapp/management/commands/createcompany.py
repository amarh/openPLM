"""
Management utility to create a "company" user.
"""

import getpass
import os
import re
import sys
from optparse import make_option
from django.contrib.auth.models import User
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from django.utils import importlib

from openPLM.plmapp.models import GroupInfo

RE_VALID_USERNAME = re.compile('[\w.@+-]+$')

EMAIL_RE = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"' # quoted-string
    r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain

def is_valid_email(value):
    if not EMAIL_RE.search(value):
        raise exceptions.ValidationError(_('Enter a valid e-mail address.'))

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--company', dest='company', default=None,
            help='Specifies the company.'),
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind. '    \
                 'You must use --username and --email with --noinput, and '      \
                 'superusers created with --noinput will not be able to log in '  \
                 'until they\'re given a valid password.'),
    )
    help = 'Used to create a "company" user.'

    def handle(self, *args, **options):
        from django.conf import settings
        username = options.get('company', None)
        interactive = options.get('interactive')

        # Do quick and dirty validation if --noinput
        if not interactive:
            if not username:
                raise CommandError("You must use --company with --noinput.")
            if not RE_VALID_USERNAME.match(username):
                raise CommandError("Invalid username. Use only letters, digits, and underscores")

        password = ''

        # Try to determine the current system user's username to use as a default.
        try:
            default_username = settings.COMPANY
            found = True
        except AttributeError:
            default_username = 'company'
            found = False

        # Determine whether the default username is taken, so we don't display
        # it as an option.
        if default_username:
            try:
                User.objects.get(username=default_username)
            except User.DoesNotExist:
                pass
            else:
                default_username = ''

        # Prompt for username/email/password. Enclose this whole thing in a
        # try/except to trap for a keyboard interrupt and exit gracefully.
        if interactive:
            try:

                # Get a username
                while 1:
                    if not username:
                        input_msg = 'Username'
                        if default_username:
                            input_msg += ' (Leave blank to use %r)' % default_username
                        username = raw_input(input_msg + ': ')
                    if default_username and username == '':
                        username = default_username
                    if not RE_VALID_USERNAME.match(username):
                        sys.stderr.write("Error: That username is invalid. Use only letters, digits and underscores.\n")
                        username = None
                        continue
                    try:
                        User.objects.get(username=username)
                    except User.DoesNotExist:
                        break
                    else:
                        sys.stderr.write("Error: That username is already taken.\n")
                        username = None

                # Get a password
                while 1:
                    if not password:
                        password = getpass.getpass()
                        password2 = getpass.getpass('Password (again): ')
                        if password != password2:
                            sys.stderr.write("Error: Your passwords didn't match.\n")
                            password = None
                            continue
                    if password.strip() == '':
                        sys.stderr.write("Error: Blank passwords aren't allowed.\n")
                        password = None
                        continue
                    break

            except KeyboardInterrupt:
                sys.stderr.write("\nOperation cancelled.\n")
                sys.exit(1)

        cie = User.objects.create(username=username)
        cie.set_password(password)
        try:
            gr = GroupInfo.objects.get(name="leading_group")
            gr.owner = cie
            gr.creator = cie
            gr.save()
        except GroupInfo.DoesNotExist:
            gr = GroupInfo.objects.create(name="leading_group", owner=cie,
                    creator=cie)

        cie.groups.add(gr)
        cie.save()
        p = cie.profile
        p.is_contributor = True
        p.save()

        print "Company created successfully."

        if not found or default_username != username:
            try:
                add = raw_input("Add company to settings file [yes|no] ? ")
                while 1:
                    if add not in ("yes", "no"):
                        add = raw_input('Please enter either "yes" or "no": ')
                        continue
                    if add == 'yes':
                        mod =  importlib.import_module(settings.SETTINGS_MODULE)
                        path = os.path.splitext(mod.__file__)[0] + ".py"
                        with file(path, "a") as f:
                            f.write("\nCOMPANY = '%s'\n" % username)
                    break
            except KeyboardInterrupt:
                sys.stderr.write("\nOperation cancelled.\n")
                sys.exit(1)

