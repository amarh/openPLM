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

"""
This small module register all plmapp models for the admin interface
"""

from django.db import models
from django.contrib import admin

import openPLM.plmapp.models as m

# register all the models from plmapp
# we browse all attributes from plmapp.models
# if an attribute derives from models.Models and the model is not abstract,
# we register it
for attr in dir(m):
    try:
        obj = getattr(m, attr)
        if issubclass(obj, models.Model) and not obj._meta.abstract:
            admin.site.register(obj)
    except (TypeError, admin.sites.AlreadyRegistered), e:
        continue
