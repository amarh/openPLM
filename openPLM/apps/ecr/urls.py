from django.urls import re_path
from django.conf import settings
from django.conf.urls import *
import openPLM.apps.ecr.views as views
import openPLM.apps.ecr.controllers
import openPLM.plmapp.views as pviews
import openPLM.apps.pdfgen.views as view


ecr = r'^ecr/(?P<obj_ref>%(x)s)/' % {'x': r'[^/?#\t\r\v\f]+'}

ecr_dict = {"obj_type": "ECR", "obj_revi": "-"}

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

urlpatterns = [
    re_path(ecr + "(?:attributes/)?$", pviews.display_object_attributes, ecr_dict),
    re_path(r"^pdf/" + ecr[1:] + "(?:attributes/)?$", view.attributes, ecr_dict),
    re_path(ecr + r"history/$", pviews.display_object_history, ecr_dict),
    re_path(ecr + r"history/$", pviews.display_object_history, ecr_dict),
    re_path(ecr + r"lifecycle/$", pviews.display_object_lifecycle, ecr_dict),
    re_path(ecr + r"lifecycle/apply/$", pviews.display_object_lifecycle, ecr_dict),
    re_path(ecr + r'management/add/$', pviews.add_management, ecr_dict),
    re_path(ecr + r'management/add-reader/$', pviews.add_management, dict(obj_type="ECR",obj_revi="-", reader=True)),
    re_path(ecr + r'management/add-signer(?P<level>\d+)/$', pviews.add_management, ecr_dict),
    re_path(ecr + r'management/replace/(?P<link_id>\d+)/$', pviews.replace_management, ecr_dict),
    re_path(ecr + r'management/delete/$', pviews.delete_management, ecr_dict),
    re_path(ecr + r'part-doc-cads/$', views.plmobjects),
    re_path(ecr + r'part-doc-cads/add/$', views.attach_plmobject),
    re_path(ecr + r'part-doc-cads/delete/$', views.detach_plmobject),
    re_path(r'^browse/ecr/$', views.browse_ecr),
    re_path(r'^history_item/ecr/(?P<hid>\d+)/$', views.redirect_history),
    re_path(r'^object/' + object_pattern + "changes/$", views.changes),
    re_path(r'^ajax/richtext_preview/' + ecr[1:] +"-/$", pviews.ajax_richtext_preview, ecr_dict),
    re_path(r'^ajax/navigate/ECR/(?P<obj_ref>%(x)s)/?' % {'x': r'[^/?#\t\r\v\f]+'}, pviews.ajax_navigate, ecr_dict),
    re_path(ecr + r'navigate/?$', pviews.navigate, ecr_dict),]

if "openPLM.apps.rss" in settings.INSTALLED_APPS:
    from openPLM.apps.rss.feeds import RssFeed, AtomFeed
    urlpatterns +=[
        re_path(ecr+ "rss/$", RssFeed(), ecr_dict),
        re_path(ecr + "atom/$", AtomFeed(), ecr_dict),]