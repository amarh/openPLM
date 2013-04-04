"""
Management utility to sponsor a new user.
"""

from optparse import make_option
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from openPLM.plmapp.forms import SponsorForm
from openPLM.plmapp.models import GroupInfo
from openPLM.plmapp.controllers import UserController

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--sponsor', default=None,
            help='Specifies the sponsor.'),
        make_option('--username', default=None,
            help='Specifies the username.'),
        make_option('--role', default=SponsorForm.ROLES[0][0],
            choices=[r[0] for r in SponsorForm.ROLES],
            help='Specifies the user role.'),
        make_option('--email', default=None,
            help='Specifies the email.'),
        make_option('--groups', default=None, action="append",
            help='Specifies the groups.'),
        make_option('--first_name', default=None,
            help='Specifies the first name.'),
        make_option('--last_name', default=None,
            help='Specifies the last name.'),
        make_option('--language', default='en',
            help='Specifies the language.'),

    )

    args = '--sponsor=<username> --username=<new_username> --email=<e@e.net> --groups=<g1> --groups=<g2> --first_name=<fn> --last_name=<ln>'
    help = 'Used to sponsor a new user'

    def handle(self, *args, **options):
        sponsor = User.objects.get(username=options.get('sponsor', None))
        obj = UserController(sponsor, sponsor)
        data = dict(options)
        data["sponsor"] = sponsor.id
        data["warned"] = True
        data["groups"] = list(GroupInfo.objects.filter(name__in=options["groups"]).values_list("id", flat=True))
        form = SponsorForm(data)
        if form.is_valid():
            new_user = form.save()
            new_user.profile.language = form.cleaned_data["language"]
            role = form.cleaned_data["role"]
            obj.sponsor(new_user, role=="contributor", role=="restricted")
        else:
            raise CommandError(form.errors.as_text())

