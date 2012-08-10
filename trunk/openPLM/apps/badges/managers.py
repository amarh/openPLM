from django.db import models

class BadgeManager(models.Manager):
    def active(self):
        import openPLM.apps.badges
        return self.get_query_set().filter(id__in=openPLM.apps.badges.registered_badges.keys())
        
