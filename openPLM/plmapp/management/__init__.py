"""
Creates a company if needs.
"""

from django.db.models import signals
from openPLM.plmapp import models as plm_app

def create_company(app, created_models, verbosity, **kwargs):
    from django.contrib.auth.models import User
    from django.core.management import call_command
    if User in created_models and kwargs.get('interactive', True):
        msg = "\nYou just installed openPLM system, which means you don't have " \
                "any companies defined.\nWould you like to create one now? (yes/no): "
        confirm = raw_input(msg)
        while 1:
            if confirm not in ('yes', 'no'):
                confirm = raw_input('Please enter either "yes" or "no": ')
                continue
            if confirm == 'yes':
                call_command("createcompany", interactive=True)
            break

signals.post_syncdb.connect(create_company,
    sender=plm_app, dispatch_uid = "openPLM.plmapp.management.create_company")
