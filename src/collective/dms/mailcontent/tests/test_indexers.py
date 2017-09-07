# -*- coding: utf8 -*-

import unittest2 as unittest
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from z3c.relationfield.relation import RelationValue

from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from plone.dexterity.utils import createContentInContainer

from collective.dms.mailcontent.testing import INTEGRATION
from ..indexers import sender_index, recipients_index


class TestIndexers(unittest.TestCase):
    """Base class to test new content types"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.intids = getUtility(IIntIds)
        setup = api.portal.get_tool('portal_setup')
        setup.runImportStepFromProfile('profile-collective.contact.core:test_data',
                                       'collective.contact.core-createTestData')
        self.mydirectory = self.portal['mydirectory']
        self.armeedeterre = self.mydirectory['armeedeterre']
        self.corpsa = self.armeedeterre['corpsa']
        self.divisionalpha = self.corpsa['divisionalpha']
        self.degaulle = self.mydirectory['degaulle']
        self.general = self.degaulle['gadt']
        self.omail1 = createContentInContainer(self.portal, 'dmsoutgoingmail',
                                               **{'title': 'Test 1',
                                                  'sender': RelationValue(self.intids.getId(self.general)),
                                                  'recipients': [RelationValue(self.intids.getId(self.general))]})
        self.imail1 = createContentInContainer(self.portal, 'dmsincomingmail',
                                               **{'title': 'Test 1',
                                                  'sender': [RelationValue(self.intids.getId(self.general)),
                                                             RelationValue(self.intids.getId(self.divisionalpha))],
                                                  'recipients': [RelationValue(self.intids.getId(self.general))]})

    def test_sender_index(self):
        # test outgoingmail
        indexer = sender_index(self.omail1)
        # test with held_position
        index_value = indexer()
        self.assertEqual(len(index_value), 2)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn('l:%s' % self.armeedeterre.UID(), index_value)
        # test with organization
        self.omail1.sender = RelationValue(self.intids.getId(self.divisionalpha))
        index_value = indexer()
        self.assertEqual(len(index_value), 4)
        self.assertIn(self.divisionalpha.UID(), index_value)
        self.assertIn('l:%s' % self.divisionalpha.UID(), index_value)
        self.assertIn('l:%s' % self.corpsa.UID(), index_value)
        self.assertIn('l:%s' % self.armeedeterre.UID(), index_value)
        # test incomingmail
        indexer = sender_index(self.imail1)
        # test with held_position
        index_value = indexer()
        self.assertEqual(len(index_value), 5)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn('l:%s' % self.armeedeterre.UID(), index_value)
        # test with organization
        self.assertIn(self.divisionalpha.UID(), index_value)
        self.assertIn('l:%s' % self.divisionalpha.UID(), index_value)
        self.assertIn('l:%s' % self.corpsa.UID(), index_value)
        self.assertIn('l:%s' % self.armeedeterre.UID(), index_value)

    def test_recipients_index(self):
        indexer = recipients_index(self.omail1)
        # test with held_position
        index_value = indexer()
        self.assertEqual(len(index_value), 2)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn('l:%s' % self.armeedeterre.UID(), index_value)
        # test with organization
        self.omail1.recipients.append(RelationValue(self.intids.getId(self.divisionalpha)))
        index_value = indexer()
        self.assertEqual(len(index_value), 5)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn(self.divisionalpha.UID(), index_value)
        self.assertIn('l:%s' % self.divisionalpha.UID(), index_value)
        self.assertIn('l:%s' % self.corpsa.UID(), index_value)
        self.assertIn('l:%s' % self.armeedeterre.UID(), index_value)
