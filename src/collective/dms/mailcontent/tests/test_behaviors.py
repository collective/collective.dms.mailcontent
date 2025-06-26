# -*- coding: utf8 -*-
from collective.dms.mailcontent.behaviors import ISendingType
from collective.dms.mailcontent.testing import INTEGRATION
from ecreall.helpers.testing.base import BaseTest
from plone.app.testing.helpers import setRoles
from plone.app.testing.interfaces import TEST_USER_ID
from plone.app.testing.interfaces import TEST_USER_NAME
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from zope.component import getUtility

import unittest


class TestBehaviors(unittest.TestCase, BaseTest):
    """Tests behaviors"""

    layer = INTEGRATION

    def setUp(self):
        super(TestBehaviors, self).setUp()
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.login(TEST_USER_NAME)
        self.portal.invokeFactory("testtype", "testitem")
        self.testitem = self.portal["testitem"]

    def test_behaviors_installation(self):
        sending_type_behavior = getUtility(IBehavior, name="collective.dms.mailcontent.behaviors.ISendingType")
        self.assertEqual(sending_type_behavior.interface, ISendingType)
        IFormFieldProvider.providedBy(sending_type_behavior.interface)

    def test_sending_type_fields(self):
        item = self.testitem
        self.assertTrue(hasattr(item, "sending_type"))
        self.assertEqual(item.sending_type, "normal")
        item.sending_type = "registered"
        self.assertEqual(item.sending_type, "registered")
