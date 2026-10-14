"""browser/views.py"""

from collective.dms.mailcontent.browser.views import AddOM
from collective.dms.mailcontent.browser.views import DmsOutgoingMailUpdateWidgets
from collective.dms.mailcontent.browser.views import OMCustomAddForm
from collective.dms.mailcontent.browser.views import OMEdit
from collective.dms.mailcontent.testing import FUNCTIONAL
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.tests.base import clean_request
from collective.dms.mailcontent.tests.base import OM_EDIT_IRN
from collective.dms.mailcontent.tests.base import OM_INCREMENT
from collective.dms.mailcontent.tests.base import OM_NUMBER
from collective.dms.mailcontent.tests.base import set_form
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.dexterity.utils import createContent
from plone.testing.zope import Browser
from unittest.mock import patch
from zExceptions import Unauthorized

import transaction
import unittest


class ViewsTestCase(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.folder = api.content.create(
            container=self.portal, type="Folder", id="folder", title="Folder"
        )
        self.om = api.content.create(
            container=self.folder, type="dmsoutgoingmail", id="om", title="O mail"
        )
        setRoles(self.portal, TEST_USER_ID, ["Contributor", "Editor"])

    def settings(self, edit_irn, increment=True):
        api.portal.set_registry_record(OM_EDIT_IRN, edit_irn)
        api.portal.set_registry_record(OM_INCREMENT, increment)
        set_form(self.request)
        clean_request(self.request)

    def add_form(self):
        form = self.folder.restrictedTraverse("++add++dmsoutgoingmail").form_instance
        form.update()
        return form

    def edit_form(self):
        form = self.om.restrictedTraverse("@@dmsdocument-edit")
        form.update()
        return form

    def irn_flags(self):
        return self.request.get("_hide_irn"), self.request.get("_auto_ref")


class TestViews(ViewsTestCase):
    """Module functions"""

    def test_DmsOutgoingMailUpdateWidgets(self):
        self.settings("show")
        form = self.add_form()
        widget = form.widgets["internal_reference_no"]
        self.assertEqual(form.current_user.getId(), TEST_USER_ID)
        self.assertEqual((widget.mode, widget.value), ("input", "test-out/11"))
        # hidden for a non manager, emptied in the add form: the number is set at creation
        self.request["_hide_irn"] = True
        DmsOutgoingMailUpdateWidgets(form)
        self.assertEqual((widget.mode, widget.value), ("hidden", ""))
        # kept in the edit form
        form = self.edit_form()
        widget = form.widgets["internal_reference_no"]
        self.request["_hide_irn"] = True
        DmsOutgoingMailUpdateWidgets(form)
        self.assertEqual((widget.mode, widget.value), ("hidden", "test-out/10"))
        # a manager or a site administrator sees it
        for role in ("Manager", "Site Administrator"):
            setRoles(self.portal, TEST_USER_ID, [role])
            form = self.add_form()
            widget = form.widgets["internal_reference_no"]
            self.request["_hide_irn"] = True
            DmsOutgoingMailUpdateWidgets(form)
            self.assertEqual(
                (widget.mode, widget.value), ("input", "test-out/11"), role
            )


class TestOMEdit(ViewsTestCase):
    def test_is_initial_state(self):
        form = self.om.restrictedTraverse("@@dmsdocument-edit")
        self.assertIsInstance(form, OMEdit)
        # no workflow
        self.assertEqual(self.portal.portal_workflow.getWorkflowsFor(self.om), [])
        self.assertTrue(form.is_initial_state())
        self.portal.portal_workflow.setChainForPortalTypes(
            ["dmsoutgoingmail"], "intranet_workflow"
        )
        self.assertEqual(api.content.get_state(self.om), "internal")
        self.assertTrue(form.is_initial_state())
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        api.content.transition(self.om, "submit")
        self.assertFalse(form.is_initial_state())

    def test_updateFields(self):
        self.settings("show")
        self.edit_form()
        self.assertEqual(self.irn_flags(), (None, None))
        # the number is not incremented when the reference is editable
        self.settings("show", increment=False)
        self.edit_form()
        self.assertEqual(self.irn_flags(), (None, False))
        self.settings("hide", increment=False)
        self.edit_form()
        self.assertEqual(self.irn_flags(), (True, None))
        # reply: editable for a response in its initial state
        self.settings("reply", increment=False)
        self.edit_form()
        self.assertEqual(self.irn_flags(), (True, None))
        self.om._is_response = True
        self.settings("reply", increment=False)
        self.edit_form()
        self.assertEqual(self.irn_flags(), (None, False))
        self.portal.portal_workflow.setChainForPortalTypes(
            ["dmsoutgoingmail"], "intranet_workflow"
        )
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        api.content.transition(self.om, "submit")
        self.settings("reply", increment=False)
        self.edit_form()
        self.assertEqual(self.irn_flags(), (True, None))

    def test_updateWidgets(self):
        self.settings("hide")
        widget = self.edit_form().widgets["internal_reference_no"]
        self.assertEqual((widget.mode, widget.value), ("hidden", "test-out/10"))
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.settings("hide")
        widget = self.edit_form().widgets["internal_reference_no"]
        self.assertEqual((widget.mode, widget.value), ("input", "test-out/10"))


class TestOMCustomAddForm(ViewsTestCase):
    def test_updateFields(self):
        self.settings("show")
        self.add_form()
        self.assertEqual(self.irn_flags(), (None, None))
        self.settings("show", increment=False)
        self.add_form()
        self.assertEqual(self.irn_flags(), (None, False))
        for edit_irn in ("hide", "reply"):
            self.settings(edit_irn, increment=False)
            self.add_form()
            self.assertEqual(self.irn_flags(), (True, None), edit_irn)

    def test_updateWidgets(self):
        self.settings("reply")
        widget = self.add_form().widgets["internal_reference_no"]
        self.assertEqual((widget.mode, widget.value), ("hidden", ""))
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.settings("reply")
        widget = self.add_form().widgets["internal_reference_no"]
        self.assertEqual((widget.mode, widget.value), ("input", "test-out/11"))

    def test_add(self):
        self.settings("show", increment=False)
        form = self.add_form()
        self.assertIsInstance(form, OMCustomAddForm)
        form.add(
            createContent("dmsoutgoingmail", title="Out", internal_reference_no="S1")
        )
        om = self.folder["out"]
        self.assertFalse(om._auto_ref)
        self.assertEqual(api.portal.get_registry_record(OM_NUMBER), 11)
        self.assertEqual(form.immediate_view, "http://nohost/plone/folder/out/view")
        # with the increment
        self.settings("show")
        form = self.add_form()
        form.add(createContent("dmsoutgoingmail", title="Out 2"))
        self.assertFalse(hasattr(self.folder["out-2"], "_auto_ref"))
        self.assertEqual(self.folder["out-2"].internal_reference_no, "test-out/11")
        self.assertEqual(api.portal.get_registry_record(OM_NUMBER), 12)


class TestAddOM(unittest.TestCase):

    layer = FUNCTIONAL

    def test_add_view(self):
        portal = self.layer["portal"]
        setRoles(portal, TEST_USER_ID, ["Manager"])
        folder = api.content.create(
            container=portal, type="Folder", id="folder", title="Folder"
        )
        folder.manage_setLocalRoles(TEST_USER_ID, ["Contributor"])
        setRoles(portal, TEST_USER_ID, ["Member"])
        view = folder.restrictedTraverse("++add++dmsoutgoingmail")
        self.assertIsInstance(view, AddOM)
        self.assertIsInstance(view.form_instance, OMCustomAddForm)
        transaction.commit()
        browser = Browser(self.layer["app"])
        browser.handleErrors = False
        browser.addHeader(
            "Authorization", f"Basic {TEST_USER_NAME}:{TEST_USER_PASSWORD}"
        )
        # Plone 6: without the plone.protect auto CSRF check: the first render of a new site writes (dependencies:
        # dexterity.localroles fti localroles, imio.helpers volatile cache keys), the confirm form would be shown
        with patch("plone.protect.auto.CSRF_DISABLED", True):
            # a contributor opens the add form
            browser.open("%s/++add++dmsoutgoingmail" % folder.absolute_url())
            self.assertEqual(
                browser.getControl(name="form.widgets.internal_reference_no").value,
                "test-out/10",
            )
            self.assertIn(
                'id="form-widgets-recipients-widgets-query"', browser.contents
            )
            # the add permission is required
            self.assertRaises(
                Unauthorized,
                browser.open,
                "%s/++add++dmsoutgoingmail" % portal.absolute_url(),
            )
