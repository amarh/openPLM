############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
# 
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################


from django.conf.urls import include, patterns, url

def patterns2(view_prefix, url_prefix, *urls):
    urls2 = []
    for u in urls:
        u2 = list(u)
        u2[0] = url_prefix + u2[0]
        urls2.append(tuple(u2))
    return patterns(view_prefix, *urls2)

object_pattern = '(?P<obj_type>\w+)/(?P<obj_ref>%(x)s)/(?P<obj_revi>%(x)s)/' % {'x' : r'[^/?#\t\r\v\f]+'}

object_url = r'^object/' + object_pattern
user_url = r'^user/(?P<obj_ref>[^/]+)/'
group_url = r'^group/(?P<obj_ref>[^/]+)/'
user_dict = {'obj_type':'User', 'obj_revi':'-'}
group_dict = {'obj_type':'Group', 'obj_revi':'-'}
urlpatterns = patterns('openPLM.apps.pdfgen.views',
    (r'^pdf/object/' + object_pattern +'attributes/$', 'attributes'),
    (r'^pdf/object/' + object_pattern +'BOM-child/$', 'bom_pdf'),
    (r'^pdf/user/(?P<obj_ref>[^/]+)/attributes/$', 'attributes', user_dict),
    (r'^pdf/group/(?P<obj_ref>[^/]+)/attributes/$', 'attributes', group_dict),
)
urlpatterns += patterns2('openPLM.apps.pdfgen.views',
    object_pattern,
    (r'pdf/$', 'select_pdf'),
)
