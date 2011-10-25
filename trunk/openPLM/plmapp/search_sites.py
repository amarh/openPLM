
from django.conf import settings
for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM"):
        __import__("%s.models" % app, globals(), locals(), [], -1)

import haystack
haystack.autodiscover()


