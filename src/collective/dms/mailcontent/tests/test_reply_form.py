# -*- coding: utf8 -*-

from collective.dms.mailcontent.testing import INTEGRATION
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.i18n import translate
from zope.intid.interfaces import IIntIds

import unittest2 as unittest


class TestReplyForm(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Contributor'])
        self.folder = api.content.create(container=self.portal, type='Folder', id='folder', title='Folder')
        config = [{'name': u'ud', 'token': u'ud'}]
        self.dir = api.content.create(container=self.portal, type='directory', id='dir', title='Directory',
                                      organization_types=config, organization_levels=config,
                                      position_types=config)
        self.c1 = api.content.create(container=self.dir, type='organization', id='imio', title='IMIO')
        self.request = self.folder.REQUEST
        intids = getUtility(IIntIds)
        self.im = api.content.create(container=self.folder, type='dmsincomingmail', id='im', title=u'I mail',
                                     sender=[RelationValue(intids.getId(self.c1))], external_reference_no=u'xx/1',
                                     treating_groups=['Administrators'])
        self.view = self.im.unrestrictedTraverse('@@reply')

    def test_rf_label(self):
        self.assertEqual(translate(self.view.label), u'Reply to test-in/10 - I mail')

    def ttest_update_fields_irn(self):
        """ done in test_settings """

    def test_rf_updateFields(self):
        self.view.updateFields()
        self.assertEqual(self.view.request['form.widgets.reply_to'], ('/plone/folder/im',))
        self.assertEqual(self.view.request['form.widgets.recipients'], ('/plone/dir/imio',))

    def test_rf_updateWidgets(self):
        self.view.update()
        self.assertEqual(self.view.widgets['IDublinCore.title'].value, u'I mail')
        self.assertEqual(self.view.widgets['treating_groups'].value, ['Administrators'])
        self.assertEqual(self.view.widgets['reply_to'].value, ('/plone/folder/im',))
        self.assertEqual(self.view.widgets['recipients'].value, ('/plone/dir/imio',))
        self.assertEqual(self.view.widgets['external_reference_no'].value, u'xx/1')
        self.assertEqual(self.view.widgets['recipient_groups'].value, ())
        self.assertEqual(self.view.widgets['internal_reference_no'].value, u'test-out/10')

    def test_rf_add(self):
        setRoles(self.portal, TEST_USER_ID, ['Member', 'Manager'])
        self.view.update()
        params = {
            'IDublinCore.title': self.view.widgets['IDublinCore.title'].value,
            'treating_groups': ['Administrators'],
            'internal_reference_no': self.view.widgets['internal_reference_no'].value,
            'reply_to': [self.im],
            'recipient_groups': []
        }
        self.assertEqual(len(self.folder.objectIds()), 1)
        obj = self.view.createAndAdd(params)
        self.assertEqual(len(self.folder.objectIds()), 2)
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertListEqual(om.recipient_groups, [])
        # treating group is different from im
        params['treating_groups'] = ['Reviewers']
        obj = self.view.createAndAdd(params)
        self.assertEqual(len(self.folder.objectIds()), 3)
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertListEqual(om.recipient_groups, ['Administrators'])
