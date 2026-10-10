# -*- coding: utf-8 -*-
from collective.dms.mailcontent.setuphandlers import isNotGoodProfile
from collective.dms.mailcontent.setuphandlers import postInstall
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.tests.base import IM_EXPRESSION
from collective.dms.mailcontent.tests.base import IM_NUMBER
from collective.dms.mailcontent.tests.base import OM_EXPRESSION
from collective.dms.mailcontent.tests.base import OM_NUMBER
from plone import api

import unittest


class TestSetuphandlers(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.setup_tool = self.portal.portal_setup

    def empty_records(self):
        """As the registry step leaves the records before the post install."""
        for name, value in ((IM_NUMBER, 0), (IM_EXPRESSION, ""), (OM_NUMBER, 0), (OM_EXPRESSION, "")):
            api.portal.set_registry_record(name, value)

    def records(self):
        return [api.portal.get_registry_record(name) for name in (IM_NUMBER, IM_EXPRESSION, OM_NUMBER, OM_EXPRESSION)]

    def import_context(self, profile):
        return self.setup_tool._getImportContext("profile-collective.dms.mailcontent:%s" % profile)

    def test_isNotGoodProfile(self):
        self.assertFalse(isNotGoodProfile(self.import_context("default")))
        self.assertTrue(isNotGoodProfile(self.import_context("testing")))

    def test_postInstall(self):
        # existing values are kept (here the testing profile ones)
        postInstall(self.import_context("default"))
        self.assertEqual(self.records(), [10, "python:'test-in/'+number", 10, "python:'test-out/'+number"])
        # the step does nothing for another profile (no marker file)
        self.empty_records()
        self.setup_tool.runImportStepFromProfile(
            "profile-collective.dms.mailcontent:testing", "dmsmailcontent-postInstall", run_dependencies=False
        )
        self.assertEqual(self.records(), [0, "", 0, ""])
        # empty values get the defaults
        self.setup_tool.runImportStepFromProfile(
            "profile-collective.dms.mailcontent:default", "dmsmailcontent-postInstall", run_dependencies=False
        )
        self.assertEqual(self.records(), [1, "python:'in/'+number", 1, "python:'out/'+number"])
