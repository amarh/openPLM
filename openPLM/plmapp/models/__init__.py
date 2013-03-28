#! -*- coding:utf-8 -*-

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

u"""
Introduction
=============

Models for openPLM

This module contains openPLM's main models.

There are 5 kinds of models:
    * User and group related:
        - :class:`.UserProfile`
        - :class:`.GroupInfo`
        - :class:`.Invitation`
    * Lifecycle related models:
        - :class:`.Lifecycle`
        - :class:`.State`
        - :class:`.LifecycleStates`
        - there are some functions that may be useful:
            - :func:`.get_default_lifecycle`
            - :func:`.get_default_state`
    * History models:
        - :class:`.AbstractHistory`
        - :class:`.History`
        - :class:`.UserHistory`
        - :class:`.GroupHistory`
        - :class:`.history.StateHistory`
    * PLMObject models:
        - :class:`.PLMObject` is the base class
        - :class:`.Part`
        - :class:`.Document` and related classes:
            - :class:`.DocumentStorage` (see also :obj:`.docfs`)
            - :class:`.DocumentFile`
            - :class:`.PrivateFile`
        - functions:
            - :func:`.get_all_plmobjects`
            - :func:`.part.get_all_parts`
            - :func:`.get_all_documents`
            - :func:`.import_models`
    * :class:`.link.Link` models:
        - :class:`.RevisionLink`
        - :class:`.ParentChildLink`
        - :class:`.DocumentPartLink`
        - :class:`.DelegationLink`
        - :class:`.PLMObjectUserLink`
        - :class:`.AlternatePartSet`


Inheritance diagrams
=====================

Users and groups
----------------

.. inheritance-diagram:: openPLM.plmapp.models.user  openPLM.plmapp.models.group
    :parts: 1

Lifecycles
----------

.. inheritance-diagram:: openPLM.plmapp.models.lifecycle
    :parts: 1

PLMObjects
----------

.. inheritance-diagram::  openPLM.plmapp.models.plmobject  openPLM.plmapp.models.part openPLM.plmapp.models.document
    :parts: 1

Histories
----------

.. inheritance-diagram:: openPLM.plmapp.models.history
    :parts: 1

Links
-----

.. inheritance-diagram:: openPLM.plmapp.models.link
    :parts: 1

Classes and functions
========================

.. note::
    This module imports all the following functions and classes.

"""

import os
import fnmatch

from openPLM.plmapp.models.lifecycle import *
from openPLM.plmapp.models.group import *
from openPLM.plmapp.models.user import *
from openPLM.plmapp.models.plmobject import *
from openPLM.plmapp.models.part import *
from openPLM.plmapp.models.document import *
from openPLM.plmapp.models.history import *
from openPLM.plmapp.models.link import *

# monkey patch Comment models to select related fields
from django.contrib.comments.models import Comment
from django.contrib.comments.managers import CommentManager

class CommentManager(CommentManager):
    def get_query_set(self):
        return (super(CommentManager, self)
            .get_query_set()
            .select_related('user', 'user__profile'))
Comment.add_to_class('objects', CommentManager())

# import_models should be the last function

def import_models(force_reload=False):
    u"""
    Imports recursively all modules in directory *plmapp/customized_models*
    """

    MODELS_DIR = "customized_models"
    IMPORT_ROOT = "openPLM.plmapp.%s" % MODELS_DIR
    if __name__ != "openPLM.plmapp.models":
        # this avoids to import models twice
        return
    if force_reload or not hasattr(import_models, "done"):
        import_models.done = True
        models_dir = os.path.join(os.path.split(__file__)[0], MODELS_DIR)
        # we browse recursively models_dir
        for root, dirs, files in os.walk(models_dir):
            # we only look at python files
            for module in sorted(fnmatch.filter(files, "*.py")):
                if module == "__init__.py":
                    # these files are empty
                    continue
                # import_name should respect the format
                # 'openPLM.plmapp.customized_models.{module_name}'
                module_name = os.path.splitext(os.path.basename(module))[0]
                import_dir = root.split(MODELS_DIR, 1)[-1].replace(os.path.sep, ".")
                import_name = "%s.%s.%s" % (IMPORT_ROOT, import_dir, module_name)
                import_name = import_name.replace("..", ".")
                try:
                    __import__(import_name, globals(), locals(), [], -1)
                except ImportError, exc:
                    print "Exception in import_models", module_name, exc
                except StandardError, exc:
                    print "Exception in import_models", module_name, type(exc), exc
import_models()

