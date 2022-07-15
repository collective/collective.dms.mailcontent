# -*- coding: utf8 -*-

from collective.dms.mailcontent import dmsmail
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.vocabularies import EmailAttachmentsVocabulary
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.namedfile import NamedBlobFile
from plone.registry.interfaces import IRegistry
from z3c.relationfield import RelationValue
from zope.annotation import IAnnotations
from zope.component import getUtility

import datetime
import unittest2 as unittest
from zope.intid import IIntIds


class TestVocabularies(unittest.TestCase):
    """Test vocabularies"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.intids = getUtility(IIntIds)
        self.im1 = api.content.create(container=self.portal, type='dmsincomingmail', id='im1', title=u'I mail',
                                      treating_groups=['Administrators'])
        createContentInContainer(self.im1, 'dmsmainfile', title=u'D001', file=NamedBlobFile(filename=u'scanned.pdf'))
        createContentInContainer(self.im1, 'dmsappendixfile', title=u'A001',
                                 file=NamedBlobFile(filename=u'appendix.odt'))
        self.om1 = api.content.create(container=self.portal, type='dmsoutgoingmail', id='om1', title=u'O mail 1',
                                      treating_groups=['Administrators'])
        self.od1 = createContentInContainer(self.om1, 'dmsmainfile', title=u'D011',
                                            file=NamedBlobFile(filename=u'generated.odt'))
        createContentInContainer(self.om1, 'dmsappendixfile', title=u'A011',
                                 file=NamedBlobFile(filename=u'appendix1.pdf'))
        self.om2 = api.content.create(container=self.portal, type='dmsoutgoingmail', id='om2', title=u'O mail 2',
                                      treating_groups=['Administrators'])
        self.od2 = createContentInContainer(self.om2, 'dmsmainfile', title=u'D021',
                                            file=NamedBlobFile(filename=u'generated.odt'))
        createContentInContainer(self.om2, 'dmsappendixfile', title=u'A021',
                                 file=NamedBlobFile(filename=u'appendix2.pdf'))

    def test_EmailAttachmentsVocabulary(self):
        voc = EmailAttachmentsVocabulary()
        self.assertListEqual([t.title for t in voc(self.om1)],
                             [u'(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)',
                              u'(dmsmainfile) => D011'])
        self.od3 = createContentInContainer(self.om1, 'dmsmainfile', title=u'D012',
                                            file=NamedBlobFile(filename=u'mailing.odt'))
        annot = IAnnotations(self.od3)
        annot['documentgenerator'] = {'need_mailing': False}
        self.assertListEqual([t.title for t in voc(self.om1)],
                             [u'(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)',
                              u'(dmsmainfile) => D011',
                              u'(dmsmainfile) => D012'])
        annot['documentgenerator'] = {'need_mailing': True}
        # mailing work document is avoided
        self.assertListEqual([t.title for t in voc(self.om1)],
                             [u'(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)',
                              u'(dmsmainfile) => D011'])
        # link to im1
        self.om1.reply_to = [RelationValue(self.intids.getId(self.im1))]
        self.assertListEqual([t.title for t in voc(self.om1)],
                             [u'(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)',
                              u'(dmsmainfile) => D011',
                              u'test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)',
                              u'test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)'])
        # link to im1 and om2
        self.om1.reply_to = [RelationValue(self.intids.getId(self.im1)), RelationValue(self.intids.getId(self.om2))]
        self.assertListEqual([t.title for t in voc(self.om1)],
                             [u'(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)',
                              u'(dmsmainfile) => D011',
                              u'test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)',
                              u'test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)',
                              u'test-out/11 (dmsappendixfile) => A021  (\xab appendix2.pdf \xbb)',
                              u'test-out/11 (dmsmainfile) => D021'])
        self.od4 = createContentInContainer(self.om2, 'dmsmainfile', title=u'D022',
                                            file=NamedBlobFile(filename=u'mailing.odt'))
        annot = IAnnotations(self.od4)
        annot['documentgenerator'] = {'need_mailing': False}
        self.assertListEqual([t.title for t in voc(self.om1)],
                             [u'(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)',
                              u'(dmsmainfile) => D011',
                              u'test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)',
                              u'test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)',
                              u'test-out/11 (dmsappendixfile) => A021  (\xab appendix2.pdf \xbb)',
                              u'test-out/11 (dmsmainfile) => D021',
                              u'test-out/11 (dmsmainfile) => D022'])
        annot['documentgenerator'] = {'need_mailing': True}
        self.assertListEqual([t.title for t in voc(self.om1)],
                             [u'(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)',
                              u'(dmsmainfile) => D011',
                              u'test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)',
                              u'test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)',
                              u'test-out/11 (dmsappendixfile) => A021  (\xab appendix2.pdf \xbb)',
                              u'test-out/11 (dmsmainfile) => D021'])
