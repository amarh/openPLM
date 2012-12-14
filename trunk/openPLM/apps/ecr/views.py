from openPLM.plmapp.base_views import handle_errors, register_creation_view
from openPLM.plmapp.views import create_object

from openPLM.apps.ecr.forms import get_creation_form
from openPLM.apps.ecr.models import ECR

@handle_errors
def create_ecr(request, *args):
    if request.method == 'GET':
        creation_form = get_creation_form(request.user)
    elif request.method == 'POST':
        creation_form = get_creation_form(request.user, request.POST)
    return create_object(request, True, creation_form)
register_creation_view(ECR, create_ecr)

