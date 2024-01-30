"""
Creates a company if needs.
"""
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from openPLM.plmapp import models as plm_app
from django.contrib.auth.models import User
from django.core.management import call_command

@receiver(post_migrate, sender=plm_app)
def create_company(sender, app_config, verbosity, **kwargs):
    if User in app_config.get_models() and kwargs.get('interactive', True):
        msg = "\nYou just installed openPLM system, which means you don't have " \
                "any companies defined.\nWould you like to create one now? (yes/no): "
        confirm = input(msg)
        while True:
            if confirm not in ('yes', 'no'):
                confirm = input('Please enter either "yes" or "no": ')
                continue
            if confirm == 'yes':
                call_command("createcompany", interactive=True)
            break
