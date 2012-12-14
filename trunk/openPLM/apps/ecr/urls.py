
from django.conf.urls.defaults import *
import openPLM.apps.ecr.views as views
import openPLM.apps.ecr.controllers
import openPLM.plmapp.views as pviews

ecr = r'^ecr/(?P<obj_ref>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

ecr_dict = {"obj_type" : "ECR", "obj_revi" : "-"}

urlpatterns = patterns('',
        (ecr + "(?:attributes/)?$", pviews.display_object_attributes, ecr_dict ),
        (ecr + "history/$", pviews.display_object_history, ecr_dict ),
        (ecr + "lifecycle/$", pviews.display_object_lifecycle, ecr_dict ),
        (ecr + "lifecycle/apply/$", pviews.display_object_lifecycle, ecr_dict ),
                      )
