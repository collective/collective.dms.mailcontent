# -*- coding: utf8 -*-

import unittest2 as unittest
import datetime
from zope.component import getUtility
from zope.interface import Invalid
from plone.app.testing import setRoles, TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.registry.interfaces import IRegistry
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent import dmsmail


class TestContentTypes(unittest.TestCase):
    """Base class to test new content types"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])


class TestDmsmailMethods(TestContentTypes):

    def test_reception_date_default_value(self):
        self.assertEqual(dmsmail.receptionDateDefaultValue(''), datetime.date.today())

    def test_original_date_default_value(self):
        self.assertEqual(dmsmail.originalMailDateDefaultValue(''), datetime.date.today() - datetime.timedelta(3))

    def test_validateIndexValueUniqueness(self):
        imail1 = createContentInContainer(self.portal, 'dmsincomingmail', **{'internal_reference_no': '12345',
                                                                             'title': 'Test 1'})
        #test with container as context, value doesn't exist
        self.assertEquals(dmsmail.validateIndexValueUniqueness(self.portal, 'dmsincomingmail',
                                                               'internal_reference_number', '54321'), None)
        #test with container as context, value exists
        self.assertRaisesRegexp(Invalid, u"This value is already used", dmsmail.validateIndexValueUniqueness,
                                *[self.portal, 'dmsincomingmail', 'internal_reference_number', '12345'])
        #test with object as context, value doesn't exist
        self.assertEquals(dmsmail.validateIndexValueUniqueness(imail1, 'dmsincomingmail',
                                                               'internal_reference_number', '54321'), None)
        #test with object as context, value exists on the same object
        self.assertEquals(dmsmail.validateIndexValueUniqueness(imail1, 'dmsincomingmail',
                                                               'internal_reference_number', '12345'), None)
        #test with object as context and a sub element in the folder, value exists on the same object
        createContentInContainer(imail1, 'dmsmainfile', **{'title': 'File 1'})
        self.assertEquals(dmsmail.validateIndexValueUniqueness(imail1, 'dmsincomingmail',
                                                               'internal_reference_number', '12345'), None)
        #test with object as context, value exists on a different object too
        imail2 = createContentInContainer(self.portal, 'dmsincomingmail',
                                          **{'internal_reference_no': '12345', 'title': 'Test 2'})
        self.assertRaisesRegexp(Invalid, u"This value is already used", dmsmail.validateIndexValueUniqueness,
                                *[imail2, 'dmsincomingmail', 'internal_reference_number', '12345'])
        #test with empty value
        imail3 = createContentInContainer(self.portal, 'dmsincomingmail',
                                          **{'internal_reference_no': '', 'title': 'Test 2'})
        self.assertEquals(dmsmail.validateIndexValueUniqueness(self.portal, 'dmsincomingmail',
                                                               'internal_reference_number', ''), None)
        self.assertEquals(dmsmail.validateIndexValueUniqueness(imail3, 'dmsincomingmail',
                                                               'internal_reference_number', ''), None)

    def test_evaluateInternalReference(self):
        self.assertEquals(dmsmail.evaluateInternalReference(self.portal, self.portal.REQUEST,
                          'collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number',
                          'collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_talexpression'),
                          'test-in/10')
