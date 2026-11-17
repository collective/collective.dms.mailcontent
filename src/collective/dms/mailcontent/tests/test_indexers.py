from ..indexers import add_parent_organizations
from ..indexers import im_external_reference_number_indexer
from ..indexers import im_internal_reference_number_indexer
from ..indexers import om_external_reference_number_indexer
from ..indexers import om_internal_reference_number_indexer
from ..indexers import recipients_index
from ..indexers import relations_index
from ..indexers import sender_index
from collective.dms.mailcontent.testing import INTEGRATION
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from Products.PluginIndexes.unindex import _marker
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import modified

import unittest


class TestIndexers(unittest.TestCase):
    """Base class to test new content types"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.intids = getUtility(IIntIds)
        setup = api.portal.get_tool("portal_setup")
        setup.runImportStepFromProfile(
            "profile-collective.contact.core:test_data",
            "collective.contact.core-createTestData",
        )
        self.mydirectory = self.portal["mydirectory"]
        self.armeedeterre = self.mydirectory["armeedeterre"]
        self.corpsa = self.armeedeterre["corpsa"]
        self.divisionalpha = self.corpsa["divisionalpha"]
        self.degaulle = self.mydirectory["degaulle"]
        self.general = self.degaulle["gadt"]
        self.omail1 = createContentInContainer(
            self.portal,
            "dmsoutgoingmail",
            **{
                "title": "Test 1",
                "sender": RelationValue(self.intids.getId(self.general)),
                "recipients": [RelationValue(self.intids.getId(self.general))],
            },
        )
        self.imail1 = createContentInContainer(
            self.portal,
            "dmsincomingmail",
            **{
                "title": "Test 1",
                "sender": [
                    RelationValue(self.intids.getId(self.general)),
                    RelationValue(self.intids.getId(self.divisionalpha)),
                ],
                "recipients": [RelationValue(self.intids.getId(self.general))],
            },
        )
        self.catalog = self.portal.portal_catalog

    def found(self, **query):
        return [b.getObject() for b in self.catalog(sort_on="portal_type", **query)]

    def test_sender_index(self):
        # test outgoingmail
        indexer = sender_index(self.omail1)
        # test with held_position
        index_value = indexer()
        self.assertEqual(len(index_value), 2)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn("l:%s" % self.armeedeterre.UID(), index_value)
        # test with organization
        self.omail1.sender = RelationValue(self.intids.getId(self.divisionalpha))
        index_value = indexer()
        self.assertEqual(len(index_value), 4)
        self.assertIn(self.divisionalpha.UID(), index_value)
        self.assertIn("l:%s" % self.divisionalpha.UID(), index_value)
        self.assertIn("l:%s" % self.corpsa.UID(), index_value)
        self.assertIn("l:%s" % self.armeedeterre.UID(), index_value)
        # test incomingmail
        indexer = sender_index(self.imail1)
        # test with held_position
        index_value = indexer()
        self.assertEqual(len(index_value), 5)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn("l:%s" % self.armeedeterre.UID(), index_value)
        # test with organization
        self.assertIn(self.divisionalpha.UID(), index_value)
        self.assertIn("l:%s" % self.divisionalpha.UID(), index_value)
        self.assertIn("l:%s" % self.corpsa.UID(), index_value)
        self.assertIn("l:%s" % self.armeedeterre.UID(), index_value)
        # the catalog: a mail sent by an organization is found by its parents
        self.assertEqual(
            self.found(sender_index="l:%s" % self.corpsa.UID()), [self.imail1]
        )
        self.assertEqual(
            self.found(sender_index="l:%s" % self.armeedeterre.UID()),
            [self.imail1, self.omail1],
        )
        self.assertEqual(
            self.found(sender_index=self.general.UID()), [self.imail1, self.omail1]
        )

    def test_recipients_index(self):
        indexer = recipients_index(self.omail1)
        # test with held_position
        index_value = indexer()
        self.assertEqual(len(index_value), 2)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn("l:%s" % self.armeedeterre.UID(), index_value)
        # test with organization
        self.omail1.recipients.append(
            RelationValue(self.intids.getId(self.divisionalpha))
        )
        index_value = indexer()
        self.assertEqual(len(index_value), 5)
        self.assertIn(self.general.UID(), index_value)
        self.assertIn(self.divisionalpha.UID(), index_value)
        self.assertIn("l:%s" % self.divisionalpha.UID(), index_value)
        self.assertIn("l:%s" % self.corpsa.UID(), index_value)
        self.assertIn("l:%s" % self.armeedeterre.UID(), index_value)
        # the catalog
        self.omail1.reindexObject()
        self.assertEqual(
            self.found(recipients_index="l:%s" % self.corpsa.UID()), [self.omail1]
        )
        self.assertEqual(
            self.found(recipients_index=self.general.UID()), [self.imail1, self.omail1]
        )
        # the brain metadata
        brain = self.catalog(UID=self.imail1.UID())[0]
        self.assertEqual(
            sorted(brain.recipients_index),
            sorted([self.general.UID(), "l:%s" % self.armeedeterre.UID()]),
        )

    def test_relations_index(self):
        # a person: its UID only
        self.imail1.recipients = [RelationValue(self.intids.getId(self.degaulle))]
        self.assertEqual(
            relations_index(self.imail1, "recipients"), [self.degaulle.UID()]
        )
        # each value once
        self.imail1.recipients = [
            RelationValue(self.intids.getId(self.divisionalpha)),
            RelationValue(self.intids.getId(self.corpsa)),
        ]
        self.assertEqual(
            sorted(relations_index(self.imail1, "recipients")),
            sorted(
                [
                    self.divisionalpha.UID(),
                    self.corpsa.UID(),
                    "l:%s" % self.divisionalpha.UID(),
                    "l:%s" % self.corpsa.UID(),
                    "l:%s" % self.armeedeterre.UID(),
                ]
            ),
        )
        # nothing to index
        self.imail1.recipients = []
        self.assertIs(relations_index(self.imail1, "recipients"), _marker)
        self.imail1.recipients = None
        self.assertIs(relations_index(self.imail1, "recipients"), _marker)
        document = createContentInContainer(self.portal, "dmsdocument", title="Doc")
        self.assertIs(relations_index(document, "sender"), _marker)
        self.assertIs(sender_index(document)(), _marker)
        # a broken relation (deleted contact) is skipped
        person = api.content.create(
            container=self.mydirectory, type="person", id="temp", lastname="Temp"
        )
        person_intid = self.intids.getId(person)
        self.imail1.recipients = [RelationValue(person_intid)]
        modified(self.imail1)
        # (deletion not stopped by the link integrity check, as when the user confirms it)
        # Plone 6: plone.api checks it itself (Plone 4: site_properties enable_link_integrity_checks)
        api.content.delete(person, check_linkintegrity=False)
        self.assertTrue(self.imail1.recipients[0].isBroken())
        self.assertIs(relations_index(self.imail1, "recipients"), _marker)
        # a dangling relation (target gone, not marked broken) is skipped too
        self.imail1.recipients = [RelationValue(person_intid)]
        self.assertFalse(self.imail1.recipients[0].isBroken())
        self.assertIsNone(self.imail1.recipients[0].to_object)
        self.assertIs(relations_index(self.imail1, "recipients"), _marker)
        self.imail1.recipients.append(RelationValue(self.intids.getId(self.degaulle)))
        self.assertEqual(
            relations_index(self.imail1, "recipients"), [self.degaulle.UID()]
        )

    def test_add_parent_organizations(self):
        index = ["x"]
        add_parent_organizations(self.divisionalpha, index)
        self.assertEqual(
            index,
            [
                "x",
                "l:%s" % self.armeedeterre.UID(),
                "l:%s" % self.corpsa.UID(),
                "l:%s" % self.divisionalpha.UID(),
            ],
        )

    def test_im_internal_reference_number_indexer(self):
        self.assertEqual(self.imail1.internal_reference_no, "test-in/10")
        self.assertEqual(
            im_internal_reference_number_indexer(self.imail1)(), "test-in/10"
        )
        # not acquired by the files of the mail
        createContentInContainer(self.imail1, "dmsmainfile", title="1")
        self.assertEqual(
            self.found(internal_reference_number="test-in/10"), [self.imail1]
        )
        self.assertEqual(
            self.catalog(UID=self.imail1.UID())[0].internal_reference_number,
            "test-in/10",
        )
        self.imail1.internal_reference_no = None
        self.assertIs(im_internal_reference_number_indexer(self.imail1)(), _marker)
        self.imail1.reindexObject()
        self.assertEqual(self.found(internal_reference_number="test-in/10"), [])

    def test_om_internal_reference_number_indexer(self):
        self.assertEqual(
            om_internal_reference_number_indexer(self.omail1)(), "test-out/10"
        )
        createContentInContainer(self.omail1, "dmsmainfile", title="1")
        self.assertEqual(
            self.found(internal_reference_number="test-out/10"), [self.omail1]
        )
        self.omail1.internal_reference_no = ""
        self.assertIs(om_internal_reference_number_indexer(self.omail1)(), _marker)

    def test_im_external_reference_number_indexer(self):
        self.assertIs(im_external_reference_number_indexer(self.imail1)(), _marker)
        self.imail1.external_reference_no = "ext/1"
        self.imail1.reindexObject()
        self.assertEqual(im_external_reference_number_indexer(self.imail1)(), "ext/1")
        createContentInContainer(self.imail1, "dmsmainfile", title="1")
        self.assertEqual(self.found(external_reference_number="ext/1"), [self.imail1])

    def test_om_external_reference_number_indexer(self):
        self.assertIs(om_external_reference_number_indexer(self.omail1)(), _marker)
        self.omail1.external_reference_no = "ext/2"
        self.omail1.reindexObject()
        self.assertEqual(om_external_reference_number_indexer(self.omail1)(), "ext/2")
        createContentInContainer(self.omail1, "dmsmainfile", title="1")
        self.assertEqual(self.found(external_reference_number="ext/2"), [self.omail1])
