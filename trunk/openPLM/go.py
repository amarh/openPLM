from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.forms import *

user = User.objects.all()[0]
p = Part.objects.all()[0]
c = PLMObjectController(p, user)
