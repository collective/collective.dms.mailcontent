# -*- coding: utf8 -*-

from collective.dms.basecontent.dmsdocument import IDmsDocument
from collective.dms.mailcontent import dmsmail
from collective.dms.mailcontent.testing import INTEGRATION
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.registry.interfaces import IRegistry
from z3c.relationfield import RelationValue
from zope.component import getUtility
from zope.interface import Invalid
from zope.intid import IIntIds
from zope.lifecycleevent import modified

import datetime
import unittest2 as unittest


class TestContentTypes(unittest.TestCase):
    """Base class to test new content types"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.folder = api.content.create(container=self.portal, type="Folder", id="folder", title="Folder")


class TestDmsmailMethods(TestContentTypes):
    def test_reception_date_default_value(self):
        reception_date = dmsmail.receptionDateDefaultValue("")
        current_date = datetime.datetime.now()
        self.assertEqual(reception_date.date(), current_date.date())
        self.assertEqual(reception_date.hour, current_date.hour)
        self.assertEqual(reception_date.minute, current_date.minute)

    def test_original_date_default_value(self):
        self.assertEqual(dmsmail.originalMailDateDefaultValue(""), datetime.date.today() - datetime.timedelta(3))

    def test_validateIndexValueUniqueness(self):
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        # test with container as context, value doesn't exist
        self.assertEquals(
            dmsmail.validateIndexValueUniqueness(
                self.portal, dmsmail.IDmsIncomingMail, "internal_reference_number", "54321"
            ),
            None,
        )
        # test with container as context, value exists
        self.assertRaisesRegexp(
            Invalid,
            u"This value is already used",
            dmsmail.validateIndexValueUniqueness,
            *[self.portal, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345"]
        )
        # test with object as context, value doesn't exist
        self.assertEquals(
            dmsmail.validateIndexValueUniqueness(
                imail1, dmsmail.IDmsIncomingMail, "internal_reference_number", "54321"
            ),
            None,
        )
        # test with object as context, value exists on the same object
        self.assertEquals(
            dmsmail.validateIndexValueUniqueness(
                imail1, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345"
            ),
            None,
        )
        # test with object as context and a sub element in the folder, value exists on the same object
        createContentInContainer(imail1, "dmsmainfile", **{"title": "File 1"})
        self.assertEquals(
            dmsmail.validateIndexValueUniqueness(
                imail1, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345"
            ),
            None,
        )
        # test with object as context, value exists on a different object too
        imail2 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 2"}
        )
        self.assertRaisesRegexp(
            Invalid,
            u"This value is already used",
            dmsmail.validateIndexValueUniqueness,
            *[imail2, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345"]
        )
        # test with empty value
        imail3 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "", "title": "Test 2"}
        )
        self.assertEquals(
            dmsmail.validateIndexValueUniqueness(
                self.portal, dmsmail.IDmsIncomingMail, "internal_reference_number", ""
            ),
            None,
        )
        self.assertEquals(
            dmsmail.validateIndexValueUniqueness(imail3, dmsmail.IDmsIncomingMail, "internal_reference_number", ""),
            None,
        )

    def test_evaluateInternalReference(self):
        self.assertEquals(
            dmsmail.evaluateInternalReference(
                self.portal,
                self.portal.REQUEST,
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number",
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_talexpression",
            ),
            "test-in/10",
        )

    def test_incrementIncomingMailNumber(self):
        registry = getUtility(IRegistry)
        old_value = registry["collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number"]
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        self.assertEquals(
            registry["collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number"], old_value + 1
        )
        self.assertEquals(imail1.internal_reference_no, "12345")
        # we create a dmsincomingmail without internal_reference_no, it will be generated
        imail2 = createContentInContainer(self.portal, "dmsincomingmail", **{"title": "Test 2"})
        self.assertEquals(imail2.internal_reference_no, "test-in/11")

    def test_title(self):
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        self.assertEquals(imail1.Title(), "12345 - Test 1")

    def test_indexes(self):
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        # get brain
        brains = self.portal.portal_catalog(path="/".join(imail1.getPhysicalPath()))
        self.assertEquals(len(brains), 1)
        self.assertEquals(imail1, brains[0].getObject())
        # search by title
        brains = self.portal.portal_catalog(Title="12345")
        self.assertEquals(len(brains), 1)
        self.assertEquals(imail1, brains[0].getObject())
        # search by SearchableText: must be done in doc tests or robot
        brains = self.portal.portal_catalog(SearchableText="12345")

    def test_get_replied(self):
        intids = getUtility(IIntIds)
        imail1 = createContentInContainer(self.folder, "dmsincomingmail", **{"title": "In 1"})
        imail2 = createContentInContainer(self.folder, "dmsincomingmail", **{"title": "In 2"})
        omail1 = createContentInContainer(self.folder, "dmsoutgoingmail", **{"title": "Out 1"})
        omail2 = createContentInContainer(self.folder, "dmsoutgoingmail", **{"title": "Out 2"})
        self.assertEqual(omail1.get_replied(), None)
        omail1.reply_to = [RelationValue(intids.getId(imail1))]
        modified(omail1)
        self.assertEqual(omail1.get_replied(), imail1)
        omail1.reply_to = [RelationValue(intids.getId(imail2)), RelationValue(intids.getId(imail1))]
        modified(omail1)
        self.assertEqual(omail1.get_replied(), imail2)
        self.assertListEqual(omail1.get_replied(first=False), [imail2, imail1])
        imail2.reply_to = [RelationValue(intids.getId(omail2))]
        modified(imail2)
        self.assertEqual(omail2.get_replied(), imail2)
        omail2.reply_to = [RelationValue(intids.getId(omail1))]
        modified(omail2)
        self.assertEqual(omail2.get_replied(), imail2)
        self.assertEqual(omail2.get_replied(intf=IDmsDocument), omail1)
