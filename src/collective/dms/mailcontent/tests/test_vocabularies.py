# -*- coding: utf8 -*-

from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.vocabularies import EmailAttachmentsVocabulary
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.namedfile import NamedBlobFile
from z3c.relationfield import RelationValue
from zope.annotation import IAnnotations
from zope.component import getUtility
from zope.intid import IIntIds

import unittest


class TestVocabularies(unittest.TestCase):
    """Test vocabularies"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.intids = getUtility(IIntIds)
        self.im1 = api.content.create(
            container=self.portal, type="dmsincomingmail", id="im1", title="I mail", treating_groups=["Administrators"]
        )
        createContentInContainer(self.im1, "dmsmainfile", title="D001", file=NamedBlobFile(filename="scanned.pdf"))
        createContentInContainer(self.im1, "dmsappendixfile", title="A001", file=NamedBlobFile(filename="appendix.odt"))
        self.om1 = api.content.create(
            container=self.portal,
            type="dmsoutgoingmail",
            id="om1",
            title="O mail 1",
            treating_groups=["Administrators"],
        )
        self.od1 = createContentInContainer(
            self.om1, "dmsmainfile", title="D011", file=NamedBlobFile(filename="generated.odt")
        )
        createContentInContainer(
            self.om1, "dmsappendixfile", title="A011", file=NamedBlobFile(filename="appendix1.pdf")
        )
        self.om2 = api.content.create(
            container=self.portal,
            type="dmsoutgoingmail",
            id="om2",
            title="O mail 2",
            treating_groups=["Administrators"],
        )
        self.od2 = createContentInContainer(
            self.om2, "dmsmainfile", title="D021", file=NamedBlobFile(filename="generated.odt")
        )
        createContentInContainer(
            self.om2, "dmsappendixfile", title="A021", file=NamedBlobFile(filename="appendix2.pdf")
        )

    def test_EmailAttachmentsVocabulary(self):
        voc = EmailAttachmentsVocabulary()
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            ["(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)", "(dmsmainfile) => D011"],
        )
        self.od3 = createContentInContainer(
            self.om1, "dmsmainfile", title="D012", file=NamedBlobFile(filename="mailing.odt")
        )
        annot = IAnnotations(self.od3)
        annot["documentgenerator"] = {"need_mailing": False}
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            [
                "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
                "(dmsmainfile) => D011",
                "(dmsmainfile) => D012",
            ],
        )
        annot["documentgenerator"] = {"need_mailing": True}
        # mailing work document is avoided
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            ["(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)", "(dmsmainfile) => D011"],
        )
        # link to im1
        self.om1.reply_to = [RelationValue(self.intids.getId(self.im1))]
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            [
                "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
                "(dmsmainfile) => D011",
                "test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)",
                "test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)",
            ],
        )
        # link to im1 and om2
        self.om1.reply_to = [RelationValue(self.intids.getId(self.im1)), RelationValue(self.intids.getId(self.om2))]
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            [
                "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
                "(dmsmainfile) => D011",
                "test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)",
                "test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)",
                "test-out/11 (dmsappendixfile) => A021  (\xab appendix2.pdf \xbb)",
                "test-out/11 (dmsmainfile) => D021",
            ],
        )
        self.od4 = createContentInContainer(
            self.om2, "dmsmainfile", title="D022", file=NamedBlobFile(filename="mailing.odt")
        )
        annot = IAnnotations(self.od4)
        annot["documentgenerator"] = {"need_mailing": False}
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            [
                "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
                "(dmsmainfile) => D011",
                "test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)",
                "test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)",
                "test-out/11 (dmsappendixfile) => A021  (\xab appendix2.pdf \xbb)",
                "test-out/11 (dmsmainfile) => D021",
                "test-out/11 (dmsmainfile) => D022",
            ],
        )
        annot["documentgenerator"] = {"need_mailing": True}
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            [
                "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
                "(dmsmainfile) => D011",
                "test-in/10 (dmsappendixfile) => A001  (\xab appendix.odt \xbb)",
                "test-in/10 (dmsmainfile) => D001  (\xab scanned.pdf \xbb)",
                "test-out/11 (dmsappendixfile) => A021  (\xab appendix2.pdf \xbb)",
                "test-out/11 (dmsmainfile) => D021",
            ],
        )
