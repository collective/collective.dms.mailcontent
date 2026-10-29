"""Results of the default profile (profiles/default) and of permissions.zcml."""

from collective.dms.mailcontent.dmsmail import DmsIncomingMail
from collective.dms.mailcontent.dmsmail import DmsOutgoingMail
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.tests.base import IM_EXPRESSION
from collective.dms.mailcontent.tests.base import IM_NUMBER
from collective.dms.mailcontent.tests.base import OM_EDIT_IRN
from collective.dms.mailcontent.tests.base import OM_EXPRESSION
from collective.dms.mailcontent.tests.base import OM_INCREMENT
from collective.dms.mailcontent.tests.base import OM_NUMBER
from collective.dms.mailcontent.tests.base import OM_TODAY
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getUtility
from zope.security.interfaces import IPermission

import unittest

ALIASES = {
    "(Default)": "(dynamic view)",
    "edit": "@@edit",
    "sharing": "@@sharing",
    "view": "(selected layout)",
}
BEHAVIORS = (
    "plone.app.content.interfaces.INameFromTitle",
    "plone.app.dexterity.behaviors.metadata.IDublinCore",
)
# Plone 6: icon names of plone.staticresources (Plone 4: png resources of the package)
ICONS = {"dmsincomingmail": "box-arrow-in-down", "dmsoutgoingmail": "box-arrow-up"}
PERMISSIONS = (
    (
        "collective.dms.mailcontent.dmsincomingmail.add",
        "collective.dms.mailcontent: Add Incoming Mail",
    ),
    (
        "collective.dms.mailcontent.dmsoutgoingmail.add",
        "collective.dms.mailcontent: Add Outgoing Mail",
    ),
)


class TestDefaultProfile(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.types = self.portal.portal_types
        self.folder = api.content.create(
            container=self.portal, type="Folder", id="folder", title="Folder"
        )

    def check_mail_fti(self, fti, name):
        """FTI properties common to both mail types."""
        self.assertEqual(fti.meta_type, "Dexterity FTI")
        self.assertEqual(fti.factory, name)
        self.assertEqual(fti.add_view_expr, "string:${folder_url}/++add++%s" % name)
        self.assertEqual(fti.icon_expr, "string:%s" % ICONS[name])
        self.assertTrue(api.portal.get_registry_record("plone.icon.%s" % ICONS[name]))
        self.assertEqual(fti.schema_policy, "schema_policy_%s" % name)
        self.assertEqual(fti.schema, "")
        self.assertEqual(fti.immediate_view, "view")
        self.assertEqual(fti.default_view, "view")
        self.assertEqual(fti.view_methods, ("view",))
        self.assertFalse(fti.default_view_fallback)
        self.assertTrue(fti.global_allow)
        self.assertFalse(fti.allow_discussion)
        self.assertTrue(fti.filter_content_types)
        self.assertEqual(fti.allowed_content_types, ("dmsmainfile", "dmsappendixfile"))
        self.assertEqual(fti.getMethodAliases(), ALIASES)
        self.assertEqual(
            [(a.id, a.permissions) for a in fti.listActions()],
            [("view", ("View",)), ("edit", ("Modify portal content",))],
        )
        self.assertIn(name, [t.getId() for t in self.folder.allowedContentTypes()])
        mail = api.content.create(
            container=self.folder, type=name, id=name, title="Mail"
        )
        self.assertEqual(
            sorted([t.getId() for t in mail.allowedContentTypes()]),
            ["dmsappendixfile", "dmsmainfile"],
        )
        return mail

    def test_type_dmsincomingmail(self):
        fti = self.types.dmsincomingmail
        self.assertEqual(fti.Title(), "Incoming Mail")
        self.assertEqual(fti.Description(), "Incoming dms mail document")
        self.assertEqual(
            fti.klass, "collective.dms.mailcontent.dmsmail.DmsIncomingMail"
        )
        self.assertEqual(
            fti.add_permission, "collective.dms.mailcontent.dmsincomingmail.add"
        )
        # Plone 6: plone.textindexer (Plone 4: collective.dexteritytextindexer)
        self.assertEqual(fti.behaviors, BEHAVIORS + ("plone.textindexer",))
        mail = self.check_mail_fti(fti, "dmsincomingmail")
        self.assertIsInstance(mail, DmsIncomingMail)
        # an incoming mail does not block the local roles inheritance (a dms document does)
        self.assertFalse(mail.__ac_local_roles_block__)

    def test_type_dmsoutgoingmail(self):
        fti = self.types.dmsoutgoingmail
        self.assertEqual(fti.Title(), "Outgoing Mail")
        self.assertEqual(fti.Description(), "Outgoing dms mail document")
        self.assertEqual(
            fti.klass, "collective.dms.mailcontent.dmsmail.DmsOutgoingMail"
        )
        self.assertEqual(
            fti.add_permission, "collective.dms.mailcontent.dmsoutgoingmail.add"
        )
        # Plone 6: the text indexer behavior too, the internal reference is in the SearchableText (see test_content;
        # Plone 4: no text indexer behavior)
        self.assertEqual(fti.behaviors, BEHAVIORS + ("plone.textindexer",))
        mail = self.check_mail_fti(fti, "dmsoutgoingmail")
        self.assertIsInstance(mail, DmsOutgoingMail)
        # inherited from the dms document
        self.assertTrue(mail.__ac_local_roles_block__)

    def test_types(self):
        self.assertEqual(
            [t for t in self.types.objectIds() if t.startswith("dms")],
            [
                "dmsdocument",
                "dmsmainfile",
                "dmsappendixfile",
                "dmsincomingmail",
                "dmsoutgoingmail",
            ],
        )

    def test_catalog(self):
        catalog = self.portal.portal_catalog
        for name, meta_type in (
            ("internal_reference_number", "FieldIndex"),
            ("external_reference_number", "FieldIndex"),
            ("sender_index", "KeywordIndex"),
            ("recipients_index", "KeywordIndex"),
        ):
            index = catalog._catalog.getIndex(name)
            self.assertEqual(index.meta_type, meta_type)
            self.assertEqual(list(index.getIndexSourceNames()), [name])
        for column in ("internal_reference_number", "sender_index", "recipients_index"):
            self.assertIn(column, catalog.schema())
        self.assertNotIn("external_reference_number", catalog.schema())
        # the old sender and recipients indexes are removed
        self.assertNotIn("sender", catalog.indexes())
        self.assertNotIn("recipients", catalog.indexes())

    def test_controlpanel(self):
        configlets = {a.id: a for a in self.portal.portal_controlpanel.listActions()}
        configlet = configlets["dmsmailcontent.settings"]
        self.assertEqual(configlet.title, "Dms Mail settings")
        self.assertEqual(configlet.appId, "dmsmailcontent")
        self.assertEqual(configlet.category, "Products")
        self.assertEqual(
            configlet.getActionExpression(),
            "string:${portal_url}/@@dmsmailcontent-settings",
        )
        self.assertEqual(configlet.permissions, ("Plone Site Setup: Site",))
        # Plone 6: an icon name (Plone 4: no icon)
        self.assertEqual(configlet.getIconExpression(), "string:envelope-at")
        self.assertTrue(api.portal.get_registry_record("plone.icon.envelope-at"))
        self.assertTrue(configlet.visible)
        self.assertTrue(self.portal.restrictedTraverse("@@dmsmailcontent-settings"))

    def test_import_steps(self):
        registry = self.portal.portal_setup.getImportStepRegistry()
        step = registry.getStepMetadata("dmsmailcontent-postInstall")
        self.assertEqual(
            step["handler"], "collective.dms.mailcontent.setuphandlers.postInstall"
        )
        self.assertEqual(
            sorted(step["dependencies"]),
            ["catalog", "controlpanel", "plone.app.registry", "rolemap", "typeinfo"],
        )

    def test_metadata(self):
        setup_tool = self.portal.portal_setup
        self.assertEqual(
            setup_tool.getLastVersionForProfile("collective.dms.mailcontent:default"),
            ("11",),
        )
        # Plone 6: no plone.formwidget.datetime dependency, replaced by the plone.app.z3cform date widgets
        self.assertNotIn(
            "profile-plone.formwidget.datetime:default",
            setup_tool.getDependenciesForProfile(
                "profile-collective.dms.mailcontent:default"
            ),
        )
        for profile in (
            "plone.app.dexterity:default",
            "collective.dms.basecontent:default",
            "collective.contact.core:default",
        ):
            self.assertNotEqual(
                setup_tool.getLastVersionForProfile(profile), "unknown", profile
            )

    def test_registry(self):
        # the records of the settings schema; numbers and expressions of the testing profile
        self.assertEqual(api.portal.get_registry_record(IM_NUMBER), 10)
        self.assertEqual(
            api.portal.get_registry_record(IM_EXPRESSION), "python:'test-in/'+number"
        )
        self.assertEqual(api.portal.get_registry_record(OM_NUMBER), 10)
        self.assertEqual(
            api.portal.get_registry_record(OM_EXPRESSION), "python:'test-out/'+number"
        )
        self.assertEqual(api.portal.get_registry_record(OM_EDIT_IRN), "show")
        self.assertTrue(api.portal.get_registry_record(OM_INCREMENT))
        self.assertTrue(api.portal.get_registry_record(OM_TODAY))

    def test_rolemap(self):
        for permission_id, permission in PERMISSIONS:
            # permissions.zcml
            self.assertEqual(getUtility(IPermission, permission_id).title, permission)
            roles = [
                r["name"]
                for r in self.portal.rolesOfPermission(permission)
                if r["selected"]
            ]
            self.assertEqual(
                sorted(roles), ["Contributor", "Manager", "Site Administrator"]
            )
            self.assertTrue(self.portal.acquiredRolesAreUsedBy(permission))
        # a contributor can add mails, a member (owner of the folder) cannot
        # (local roles set before any check: borg.localrole caches them in the request)
        folder2 = api.content.create(
            container=self.portal, type="Folder", id="folder2", title="Folder 2"
        )
        folder2.manage_setLocalRoles(TEST_USER_ID, ["Owner", "Contributor"])
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        allowed = [t.getId() for t in self.folder.allowedContentTypes()]
        self.assertIn("dmsdocument", allowed)
        self.assertNotIn("dmsincomingmail", allowed)
        self.assertNotIn("dmsoutgoingmail", allowed)
        allowed = [t.getId() for t in folder2.allowedContentTypes()]
        self.assertIn("dmsincomingmail", allowed)
        self.assertIn("dmsoutgoingmail", allowed)
        for permission_id, permission in PERMISSIONS:
            self.assertTrue(api.user.has_permission(permission, obj=folder2))
            self.assertFalse(api.user.has_permission(permission, obj=self.folder))
