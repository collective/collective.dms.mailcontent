from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.vocabularies import EmailAttachmentsVocabulary
from collective.iconifiedcategory.utils import calculate_category_id
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.namedfile import NamedBlobFile
from z3c.relationfield import RelationValue
from zope.annotation import IAnnotations
from zope.component import getUtility
from zope.intid import IIntIds
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestVocabularies(unittest.TestCase):
    """Test vocabularies"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.intids = getUtility(IIntIds)
        self.im1 = api.content.create(
            container=self.portal,
            type="dmsincomingmail",
            id="im1",
            title="I mail",
            treating_groups=["Administrators"],
        )
        createContentInContainer(
            self.im1,
            "dmsmainfile",
            title="D001",
            file=NamedBlobFile(filename="scanned.pdf"),
        )
        createContentInContainer(
            self.im1,
            "dmsappendixfile",
            title="A001",
            file=NamedBlobFile(filename="appendix.odt"),
        )
        self.om1 = api.content.create(
            container=self.portal,
            type="dmsoutgoingmail",
            id="om1",
            title="O mail 1",
            treating_groups=["Administrators"],
        )
        self.od1 = createContentInContainer(
            self.om1,
            "dmsmainfile",
            title="D011",
            file=NamedBlobFile(filename="generated.odt"),
        )
        createContentInContainer(
            self.om1,
            "dmsappendixfile",
            title="A011",
            file=NamedBlobFile(filename="appendix1.pdf"),
        )
        self.om2 = api.content.create(
            container=self.portal,
            type="dmsoutgoingmail",
            id="om2",
            title="O mail 2",
            treating_groups=["Administrators"],
        )
        self.od2 = createContentInContainer(
            self.om2,
            "dmsmainfile",
            title="D021",
            file=NamedBlobFile(filename="generated.odt"),
        )
        createContentInContainer(
            self.om2,
            "dmsappendixfile",
            title="A021",
            file=NamedBlobFile(filename="appendix2.pdf"),
        )

    def add_signed_file(self, mail, title, filename):
        """A file of the "to sign" category (testing layer), signed: iconifiedcategory marks it in the mail."""
        group = self.portal["annexes_types"]["annexes"]
        group.signed_activated = True
        return createContentInContainer(
            mail,
            "dmsmainfile",
            title=title,
            file=NamedBlobFile(filename=filename),
            content_category=calculate_category_id(group["to_sign"]),
            to_sign=True,
            signed=True,
        )

    def test_EmailAttachmentsVocabulary(self):
        voc = EmailAttachmentsVocabulary()
        self.assertIsInstance(
            getUtility(
                IVocabularyFactory, "collective.dms.mailcontent.email_attachments_voc"
            ),
            EmailAttachmentsVocabulary,
        )
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            [
                "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
                "(dmsmainfile) => D011",
            ],
        )
        # the term value and token are the file UID
        self.assertEqual(
            [(t.value, t.token) for t in voc(self.om1)][1],
            (self.od1.UID(), self.od1.UID()),
        )
        self.od3 = createContentInContainer(
            self.om1,
            "dmsmainfile",
            title="D012",
            file=NamedBlobFile(filename="mailing.odt"),
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
            [
                "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
                "(dmsmainfile) => D011",
            ],
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
        self.om1.reply_to = [
            RelationValue(self.intids.getId(self.im1)),
            RelationValue(self.intids.getId(self.om2)),
        ]
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
            self.om2,
            "dmsmainfile",
            title="D022",
            file=NamedBlobFile(filename="mailing.odt"),
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
        # signed versions (categorized_elements of the mail), of the mail and of a linked mail (title by basecontent)
        signed = self.add_signed_file(self.om1, "D013", "generated.pdf")
        self.assertTrue(self.om1.categorized_elements[signed.UID()]["signed"])
        self.add_signed_file(self.om2, "D023", "generated.pdf")
        # an appendix named as its file: the file name is not repeated
        createContentInContainer(
            self.om1,
            "dmsappendixfile",
            title="plan.pdf",
            file=NamedBlobFile(filename="Plan.pdf"),
        )
        self.om1.reply_to = [RelationValue(self.intids.getId(self.om2))]
        titles = [
            "(dmsappendixfile) => A011  (\xab appendix1.pdf \xbb)",
            "(dmsappendixfile) => plan.pdf",
            "(dmsmainfile signed) => Signed version",
            "(dmsmainfile) => D011",
            "test-out/11 (dmsappendixfile) => A021  (\xab appendix2.pdf \xbb)",
            "test-out/11 (dmsmainfile signed) => Signed version",
            "test-out/11 (dmsmainfile) => D021",
        ]
        self.assertListEqual([t.title for t in voc(self.om1)], titles)
        # the files are found unrestrictedly
        self.od1.manage_permission("View", ["Manager"], acquire=False)
        self.od1.reindexObjectSecurity()
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        self.assertListEqual([t.title for t in voc(self.om1)], titles)
        # translated in the site language
        # Plone 6: registry record (Plone 4: site_properties)
        api.portal.set_registry_record("plone.default_language", "fr")
        self.assertListEqual(
            [t.title for t in voc(self.om1)],
            [
                "(A) => A011  (\xab appendix1.pdf \xbb)",
                "(A) => plan.pdf",
                "(V) => D011",
                "(VS) => Version sign\xe9e",
                "test-out/11 (A) => A021  (\xab appendix2.pdf \xbb)",
                "test-out/11 (V) => D021",
                "test-out/11 (VS) => Version sign\xe9e",
            ],
        )
