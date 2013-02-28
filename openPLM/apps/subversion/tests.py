"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""


import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

import openPLM.plmapp.exceptions as exc
import openPLM.plmapp.models as models
from openPLM.plmapp.controllers import PartController, DocumentController
from openPLM.plmapp.lifecycle import LifecycleList

from openPLM.plmapp.tests.controllers.plmobject import ControllerTest
from openPLM.plmapp.tests.views import ViewTest
from openPLM.apps.subversion.models import SubversionRepositoryController

OPENPLM_SVN_REPOSITORY = "http://openplm.org/svn/openPLM/trunk/"

class SubversionRepositoryTestCase(ControllerTest):

    TYPE = "SubversionRepository"
    CONTROLLER = SubversionRepositoryController
    DATA = {
            "repository_uri" : OPENPLM_SVN_REPOSITORY,
            "svn_revision" : "HEAD",
            "issue_tracking_system" : "path/to/trac",
            }

    def setUp(self):
        super(SubversionRepositoryTestCase, self).setUp()
        self.controller = self.CONTROLLER.create("adoc", self.TYPE, "a",
                                                 self.user, self.DATA)

    def test_is_promotable(self):
        # True even if it has no files
        self.assertTrue(self.controller.is_promotable())

    def test_command(self):
        co_cmd = "svn co -r 'HEAD' '%s'" % OPENPLM_SVN_REPOSITORY
        self.assertEqual(co_cmd, self.controller.checkout_cmd)
        exp_cmd = "svn export -r 'HEAD' '%s'" % OPENPLM_SVN_REPOSITORY
        self.assertEqual(exp_cmd, self.controller.export_cmd)

    def test_promote(self):
        self.assertEqual(self.controller.state.name, "draft")
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "official")
        # check that the revision has been updated
        self.assertTrue(int(self.controller.svn_revision) > 600)
        self.assertFalse(self.controller.is_editable)

        lcl = LifecycleList("diop", "official", "draft", 
                "issue1", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.controller.lifecycle = lc
        self.controller.state = models.State.objects.get(name="draft")
        self.controller.svn_revision = "HEAD"
        self.controller.save()
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "issue1")
        self.assertEqual("HEAD", self.controller.svn_revision)
        self.controller.demote()
        self.assertEqual(self.controller.state.name, "draft")
        self.assertTrue(self.controller.is_editable)
      
    def test_promote_with_unknown_repository(self):
        self.controller.repository_uri = "http://example.org/plop"
        self.controller.save()

        self.assertEqual(self.controller.state.name, "draft")
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "official")
        
        # should not fail even is the repository is wrong
        # the svn_revision should just not change
        self.assertEqual("HEAD", self.controller.svn_revision)
        
        self.assertFalse(self.controller.is_editable)

        lcl = LifecycleList("diop", "official", "draft", 
                "issue1", "official", "deprecated")
        lc = models.Lifecycle.from_lifecyclelist(lcl)
        self.controller.lifecycle = lc
        self.controller.state = models.State.objects.get(name="draft")
        self.controller.save()
        self.controller.promote()
        self.assertEqual(self.controller.state.name, "issue1")
        self.assertEqual("HEAD", self.controller.svn_revision)
        self.controller.demote()
        self.assertEqual(self.controller.state.name, "draft")
        self.assertTrue(self.controller.is_editable)

    def test_add_file(self):
        # must fail
        f = self.get_file()
        self.assertRaises(exc.AddFileError, self.controller.add_file, f)
        self.assertEqual(0, self.controller.files.count())

 

class SubversionRepositoryTestCase(ViewTest):

    TYPE = "SubversionRepository"
    CONTROLLER = SubversionRepositoryController
    DATA = {
            "repository_uri" : OPENPLM_SVN_REPOSITORY,
            "svn_revision" : "HEAD",
            "issue_tracking_system" : "path/to/trac",
            }

    def test_files_get(self):
        response = self.get(self.base_url + "files/", page="files")
        self.assertTemplateUsed(response, "subversion_files.html")

    def test_logs_get(self):
        response = self.get(self.base_url + "logs/", page="logs")
        self.assertTemplateUsed(response, "logs.html")
    
    def test_logs_ajax(self):
        response = self.get(self.base_url + "logs/ajax/", page="logs")
        self.assertTemplateUsed(response, "ajax_logs.html")
        self.assertFalse(response.context["error"])
        logs = response.context["logs"]
        self.assertEqual(20, len(logs))

