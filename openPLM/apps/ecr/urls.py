
from django.conf.urls.defaults import *
import openPLM.apps.ecr.views as views
import openPLM.apps.ecr.controllers
import openPLM.plmapp.views as pviews

ecr = r'^ecr/(?P<obj_ref>%(x)s)/' % {'x': r'[^/?#\t\r\v\f]+'}

ecr_dict = {"obj_type": "ECR", "obj_revi": "-"}

urlpatterns = patterns('',
    (ecr + "(?:attributes/)?$", pviews.display_object_attributes, ecr_dict),
    (ecr + "history/$", pviews.display_object_history, ecr_dict),
    (ecr + "lifecycle/$", pviews.display_object_lifecycle, ecr_dict),
    (ecr + "lifecycle/apply/$", pviews.display_object_lifecycle, ecr_dict),
    (ecr + 'management/add/$', pviews.add_management, ecr_dict),
    (ecr + 'management/add-reader/$', pviews.add_management, dict(obj_type="ECR",
                                                                obj_revi="-", reader=True)),
    (ecr + 'management/add-signer(?P<level>\d+)/$', pviews.add_management, ecr_dict),
    (ecr + 'management/replace/(?P<link_id>\d+)/$', pviews.replace_management, ecr_dict),
    (ecr + 'management/delete/$', pviews.delete_management, ecr_dict),
    ('browse/ecr/$', views.browse_ecr),
    )
