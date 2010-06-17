from openPLM.plmapp.models import *
from openPLM.plmapp.controllers import *
from openPLM.plmapp.forms import *
from openPLM.plmapp.customized_models.computer import *

user = User.objects.all()[0]
p = Part.objects.all()[0]
p2 = Part.objects.all()[1]
c = PartController(p, user)
