# usage: "from go import *" or "%run go.py" in a ./manage.py shell session
from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.forms import *
from openPLM.apps.computer.models import *

user = User.objects.all()[0]
p = Part.objects.all()[0]
p2 = Part.objects.all()[1]
c = PartController(p, user)
