
from django.conf import settings
for app in settings.INSTALLED_APPS:
    if app.startswith("openPLM"):
        __import__("%s.models" % app, globals(), locals(), [], -1)

import haystack
import sys

# little hack: autodiscover() fails if the database is not created
# but syncdb or migrate would run autodiscover without this line
if len(sys.argv) < 2 or sys.argv[1] not in ("syncdb", "migrate"):
    haystack.autodiscover()


