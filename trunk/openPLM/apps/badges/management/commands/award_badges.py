"""
Management utility to award badges to all users.
"""

import os.path

from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = 'Used to award badges if the badges apps just has been added'

    def handle(self, *args, **options):

        from django.contrib.auth.models import User
        
        import openPLM.apps.badges as b
        from openPLM.apps.badges import meta_badges
        
        badges = b.models.Badge.objects.active().order_by("level")
        users = User.objects.all()
        
        for u in users:
            for badge in badges:
                badge.award_to(u,ignore_message=True)

