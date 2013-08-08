
from django.conf import settings
from django.conf.urls import *
import openPLM.apps.ecr.views as views
import openPLM.apps.ecr.controllers
import openPLM.plmapp.views as pviews

ecr = r'^ecr/(?P<obj_ref>%(x)s)/' % {'x': r'[^/?#\t\r\v\f]+'}

ecr_dict = {"obj_type": "ECR", "obj_revi": "-"}

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

urlpatterns = patterns('',
    (ecr + "(?:attributes/)?$", pviews.display_object_attributes, ecr_dict),
    ("^pdf/" + ecr[1:] + "(?:attributes/)?$", "apps.pdfgen.views.attributes", ecr_dict),
    (ecr + r"history/$", pviews.display_object_history, ecr_dict),
    (ecr + r"history/$", pviews.display_object_history, ecr_dict),
    (ecr + r"lifecycle/$", pviews.display_object_lifecycle, ecr_dict),
    (ecr + r"lifecycle/apply/$", pviews.display_object_lifecycle, ecr_dict),
    (ecr + r'management/add/$', pviews.add_management, ecr_dict),
    (ecr + r'management/add-reader/$', pviews.add_management, dict(obj_type="ECR",
                                                                obj_revi="-", reader=True)),
    (ecr + r'management/add-signer(?P<level>\d+)/$', pviews.add_management, ecr_dict),
    (ecr + r'management/replace/(?P<link_id>\d+)/$', pviews.replace_management, ecr_dict),
    (ecr + r'management/delete/$', pviews.delete_management, ecr_dict),
    (ecr + r'part-doc-cads/$', views.plmobjects),
    (ecr + r'part-doc-cads/add/$', views.attach_plmobject),
    (ecr + r'part-doc-cads/delete/$', views.detach_plmobject),
    (r'^browse/ecr/$', views.browse_ecr),
    (r'^history_item/ecr/(?P<hid>\d+)/$', views.redirect_history),
    (r'^object/' + object_pattern + "changes/$", views.changes),
    (r'^ajax/richtext_preview/' + ecr[1:] +"-/$", "plmapp.views.ajax_richtext_preview", ecr_dict),
    (r'^ajax/navigate/ECR/(?P<obj_ref>%(x)s)/?' % {'x': r'[^/?#\t\r\v\f]+'}, pviews.ajax_navigate, ecr_dict),
    (ecr + r'navigate/?$', pviews.navigate, ecr_dict),
    )

if "openPLM.apps.rss" in settings.INSTALLED_APPS:
    from openPLM.apps.rss.feeds import RssFeed, AtomFeed
    urlpatterns += patterns("",
        (ecr + "rss/$", RssFeed(), ecr_dict),
        (ecr + "atom/$", AtomFeed(), ecr_dict),
    )

