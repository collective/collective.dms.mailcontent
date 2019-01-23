# -*- coding: utf8 -*-

from collective.dms.mailcontent.browser.reply_form import ReplyForm
from collective.dms.mailcontent.browser.views import OMCustomAddForm
from collective.dms.mailcontent.browser.views import OMEdit
from collective.dms.mailcontent.testing import INTEGRATION
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.intid.interfaces import IIntIds

import unittest2 as unittest


class TestSettings(unittest.TestCase):
    """ Base class to test views """

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

    def clean_request(self):
        for key in ('_hide_irn', '_auto_ref'):
            if key in self.request:
                self.request.other.pop(key)

    def om_params(self, view):
        return {
            'IDublinCore.title': u'test', 'internal_reference_no': view.widgets['internal_reference_no'].value,
            # 'sender': self.c1, 'recipients': [self.c1]
        }

    def test_settings(self):
        # check default config
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 10)
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_talexpression'), u"python:'test-out/'+number")
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_edit_irn'), u'show')
        self.assertTrue(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                       'outgoingmail_increment_number'))
        self.assertTrue(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                       'outgoingmail_today_mail_date'))

        # testing OM views: default parameters
        add = OMCustomAddForm(self.folder, self.request)
        add.portal_type = 'dmsoutgoingmail'
        add.update()
        self.assertNotIn('_hide_irn', self.request.keys())
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(add.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.assertEquals(add.widgets['internal_reference_no'].value, u'test-out/10')
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertFalse(hasattr(om, '_auto_ref'))
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 11)
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        self.assertNotIn('_hide_irn', self.request.keys())
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(edit.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.clean_request()

        # set outgoingmail_increment_number to False
        # => no number incrementation because irn field is editable
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_increment_number', False)
        add.update()
        self.assertNotIn('_hide_irn', self.request.keys())
        self.assertEquals(self.request['_auto_ref'], False)
        self.assertEquals(add.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.assertEquals(add.widgets['internal_reference_no'].value, u'test-out/11')
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEquals(om._auto_ref, False)
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 11)  # No increment
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        self.assertNotIn('_hide_irn', self.request.keys())
        self.assertEquals(self.request['_auto_ref'], False)
        self.assertEquals(edit.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to hide
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_edit_irn', 'hide')
        add.update()
        self.assertEquals(self.request['_hide_irn'], True)
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(add.widgets['internal_reference_no'].mode, 'hidden')
        self.assertEquals(add.widgets['internal_reference_no'].value, u'')
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEquals(om.internal_reference_no, u'test-out/11')
        self.assertFalse(hasattr(om, '_auto_ref'))
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 12)
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        self.assertEquals(self.request['_hide_irn'], True)
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(edit.widgets['internal_reference_no'].mode, 'hidden')
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to reply
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_edit_irn', 'reply')
        add.update()
        self.assertEquals(self.request['_hide_irn'], True)
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(add.widgets['internal_reference_no'].mode, 'hidden')
        self.assertEquals(add.widgets['internal_reference_no'].value, u'')
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEquals(om.internal_reference_no, u'test-out/12')
        self.assertFalse(hasattr(om, '_auto_ref'))
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 13)
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        # is not a response
        self.assertEquals(self.request['_hide_irn'], True)
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(edit.widgets['internal_reference_no'].mode, 'hidden')
        self.clean_request()
        # is a response but no workflow
        setattr(om, '_is_response', True)
        edit.update()
        self.assertEquals(api.content.get_state(om, default='no_workflow'), 'no_workflow')
        self.assertEquals(edit.is_initial_state(), True)  # has no workflow
        self.assertNotIn('_hide_irn', self.request.keys())
        self.assertEquals(self.request['_auto_ref'], False)
        self.assertEquals(edit.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.clean_request()
        # is a response, workflow and initial state
        pw = self.portal.portal_workflow
        pw.setChainForPortalTypes(['dmsoutgoingmail'], 'intranet_workflow')
        edit.update()
        self.assertEquals(api.content.get_state(om), 'internal')
        self.assertEquals(edit.is_initial_state(), True)
        self.assertNotIn('_hide_irn', self.request.keys())
        self.assertEquals(self.request['_auto_ref'], False)
        self.assertEquals(edit.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.clean_request()
        # is a response, workflow and not initial state
        api.content.transition(om, 'submit')
        edit.update()
        self.assertEquals(api.content.get_state(om), 'pending')
        self.assertEquals(edit.is_initial_state(), False)
        self.assertEquals(self.request['_hide_irn'], True)
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(edit.widgets['internal_reference_no'].mode, 'hidden')
        self.clean_request()

        # Testing reply view
        intids = getUtility(IIntIds)
        im = api.content.create(container=self.folder, type='dmsincomingmail', id='im', title=u'I mail',
                                sender=[RelationValue(intids.getId(self.c1))], external_reference_no=u'xx/1',
                                treating_groups=['Administrators'])
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_edit_irn', 'show')
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_increment_number', True)
        reply = ReplyForm(im, self.request)
        reply.update()
        self.assertEquals(self.request['_irn'], 'test-in/10')
        self.assertEquals(self.request['_hide_irn'], False)
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(reply.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.assertEquals(reply.widgets['internal_reference_no'].value, u'test-out/13')
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertFalse(hasattr(om, '_auto_ref'))
        self.assertEquals(om._is_response, True)
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 14)
        self.clean_request()

        # set outgoingmail_increment_number to False
        # => no number incrementation because irn field is editable
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_increment_number', False)
        reply.update()
        self.assertEquals(self.request['_hide_irn'], False)
        self.assertEquals(self.request['_auto_ref'], False)
        self.assertEquals(reply.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.assertEquals(reply.widgets['internal_reference_no'].value, u'test-out/14')
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEquals(om._auto_ref, False)
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 14)  # No increment
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to hide
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_edit_irn', 'hide')
        reply.update()
        self.assertEquals(self.request['_hide_irn'], True)
        self.assertNotIn('_auto_ref', self.request.keys())
        self.assertEquals(reply.widgets['internal_reference_no'].mode, 'hidden')
        self.assertEquals(reply.widgets['internal_reference_no'].value, u'')
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEquals(om.internal_reference_no, u'test-out/14')
        self.assertFalse(hasattr(om, '_auto_ref'))
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 15)
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to reply
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                       'outgoingmail_edit_irn', 'reply')
        reply.update()
        self.assertEquals(self.request['_hide_irn'], False)
        self.assertEquals(self.request['_auto_ref'], False)
        self.assertEquals(reply.widgets['internal_reference_no'].mode, 'input')  # not hidden
        self.assertEquals(reply.widgets['internal_reference_no'].value, u'test-out/15')
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEquals(om._auto_ref, False)
        self.assertEquals(api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                         'outgoingmail_number'), 15)  # No increment
        self.clean_request()
