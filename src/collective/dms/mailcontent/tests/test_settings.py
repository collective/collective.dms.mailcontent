from collective.dms.mailcontent.browser.reply_form import ReplyForm
from collective.dms.mailcontent.browser.settings import IDmsMailConfig
from collective.dms.mailcontent.browser.settings import im_irn_conditions
from collective.dms.mailcontent.browser.settings import om_irn_conditions
from collective.dms.mailcontent.browser.settings import SettingsEditForm
from collective.dms.mailcontent.browser.settings import SettingsView
from collective.dms.mailcontent.browser.views import OMCustomAddForm
from collective.dms.mailcontent.browser.views import OMEdit
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.tests.base import IM_NUMBER
from collective.dms.mailcontent.tests.base import OM_EDIT_IRN
from collective.dms.mailcontent.tests.base import OM_EXPRESSION
from collective.dms.mailcontent.tests.base import OM_INCREMENT
from collective.dms.mailcontent.tests.base import OM_TODAY
from collective.dms.mailcontent.tests.base import set_form
from DateTime import DateTime
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.supermodel.interfaces import FIELDSETS_KEY
from z3c.relationfield.relation import RelationValue
from zExceptions import Unauthorized
from zope.component import getUtility
from zope.i18n import translate
from zope.intid.interfaces import IIntIds

import unittest


class TestSettings(unittest.TestCase):
    """Base class to test views"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        self.folder = api.content.create(
            container=self.portal, type="Folder", id="folder", title="Folder"
        )
        config = [{"name": "ud", "token": "ud"}]
        self.dir = api.content.create(
            container=self.portal,
            type="directory",
            id="dir",
            title="Directory",
            organization_types=config,
            organization_levels=config,
            position_types=config,
        )
        self.c1 = api.content.create(
            container=self.dir, type="organization", id="imio", title="IMIO"
        )
        self.request = self.folder.REQUEST

    def clean_request(self):
        for key in ("_hide_irn", "_auto_ref"):
            if key in self.request:
                self.request.other.pop(key)

    def om_params(self, view):
        return {
            "IDublinCore.title": "test",
            "internal_reference_no": view.widgets["internal_reference_no"].value,
            # 'sender': self.c1, 'recipients': [self.c1]
        }

    def test_settings(self):
        # check default config
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            10,
        )
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_talexpression"
            ),
            "python:'test-out/'+number",
        )
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_edit_irn"
            ),
            "show",
        )
        self.assertTrue(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_increment_number"
            )
        )
        self.assertTrue(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_today_mail_date"
            )
        )

        # testing OM views: default parameters
        add = OMCustomAddForm(self.folder, self.request)
        add.portal_type = "dmsoutgoingmail"
        add.update()
        self.assertNotIn("_hide_irn", self.request.keys())
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(
            add.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.assertEqual(add.widgets["internal_reference_no"].value, "test-out/10")
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertFalse(hasattr(om, "_auto_ref"))
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            11,
        )
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        self.assertNotIn("_hide_irn", self.request.keys())
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(
            edit.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.clean_request()

        # set outgoingmail_increment_number to False
        # => no number incrementation because irn field is editable
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_increment_number",
            False,
        )
        add.update()
        self.assertNotIn("_hide_irn", self.request.keys())
        self.assertEqual(self.request["_auto_ref"], False)
        self.assertEqual(
            add.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.assertEqual(add.widgets["internal_reference_no"].value, "test-out/11")
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEqual(om._auto_ref, False)
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            11,
        )  # No increment
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        self.assertNotIn("_hide_irn", self.request.keys())
        self.assertEqual(self.request["_auto_ref"], False)
        self.assertEqual(
            edit.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to hide
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_edit_irn",
            "hide",
        )
        add.update()
        self.assertEqual(self.request["_hide_irn"], True)
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(add.widgets["internal_reference_no"].mode, "hidden")
        self.assertEqual(add.widgets["internal_reference_no"].value, "")
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEqual(om.internal_reference_no, "test-out/11")
        self.assertFalse(hasattr(om, "_auto_ref"))
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            12,
        )
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        self.assertEqual(self.request["_hide_irn"], True)
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(edit.widgets["internal_reference_no"].mode, "hidden")
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to reply
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_edit_irn",
            "reply",
        )
        add.update()
        self.assertEqual(self.request["_hide_irn"], True)
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(add.widgets["internal_reference_no"].mode, "hidden")
        self.assertEqual(add.widgets["internal_reference_no"].value, "")
        obj = add.createAndAdd(self.om_params(add))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEqual(om.internal_reference_no, "test-out/12")
        self.assertFalse(hasattr(om, "_auto_ref"))
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            13,
        )
        self.clean_request()
        edit = OMEdit(om, self.request)
        edit.update()
        # is not a response
        self.assertEqual(self.request["_hide_irn"], True)
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(edit.widgets["internal_reference_no"].mode, "hidden")
        self.clean_request()
        # is a response but no workflow
        setattr(om, "_is_response", True)
        edit.update()
        self.assertEqual(
            api.content.get_state(om, default="no_workflow"), "no_workflow"
        )
        self.assertEqual(edit.is_initial_state(), True)  # has no workflow
        self.assertNotIn("_hide_irn", self.request.keys())
        self.assertEqual(self.request["_auto_ref"], False)
        self.assertEqual(
            edit.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.clean_request()
        # is a response, workflow and initial state
        pw = self.portal.portal_workflow
        pw.setChainForPortalTypes(["dmsoutgoingmail"], "intranet_workflow")
        edit.update()
        self.assertEqual(api.content.get_state(om), "internal")
        self.assertEqual(edit.is_initial_state(), True)
        self.assertNotIn("_hide_irn", self.request.keys())
        self.assertEqual(self.request["_auto_ref"], False)
        self.assertEqual(
            edit.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.clean_request()
        # is a response, workflow and not initial state
        api.content.transition(om, "submit")
        edit.update()
        self.assertEqual(api.content.get_state(om), "pending")
        self.assertEqual(edit.is_initial_state(), False)
        self.assertEqual(self.request["_hide_irn"], True)
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(edit.widgets["internal_reference_no"].mode, "hidden")
        self.clean_request()

        # Testing reply view
        intids = getUtility(IIntIds)
        im = api.content.create(
            container=self.folder,
            type="dmsincomingmail",
            id="im",
            title="I mail",
            sender=[RelationValue(intids.getId(self.c1))],
            external_reference_no="xx/1",
            treating_groups=["Administrators"],
        )
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_edit_irn",
            "show",
        )
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_increment_number",
            True,
        )
        reply = ReplyForm(im, self.request)
        reply.update()
        self.assertEqual(self.request["_irn"], "test-in/10")
        self.assertEqual(self.request["_hide_irn"], False)
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(
            reply.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.assertEqual(reply.widgets["internal_reference_no"].value, "test-out/13")
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertFalse(hasattr(om, "_auto_ref"))
        self.assertEqual(om._is_response, True)
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            14,
        )
        self.clean_request()

        # set outgoingmail_increment_number to False
        # => no number incrementation because irn field is editable
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_increment_number",
            False,
        )
        reply.update()
        self.assertEqual(self.request["_hide_irn"], False)
        self.assertEqual(self.request["_auto_ref"], False)
        self.assertEqual(
            reply.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.assertEqual(reply.widgets["internal_reference_no"].value, "test-out/14")
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEqual(om._auto_ref, False)
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            14,
        )  # No increment
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to hide
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_edit_irn",
            "hide",
        )
        reply.update()
        self.assertEqual(self.request["_hide_irn"], True)
        self.assertNotIn("_auto_ref", self.request.keys())
        self.assertEqual(reply.widgets["internal_reference_no"].mode, "hidden")
        self.assertEqual(reply.widgets["internal_reference_no"].value, "")
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEqual(om.internal_reference_no, "test-out/14")
        self.assertFalse(hasattr(om, "_auto_ref"))
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            15,
        )
        self.clean_request()

        # set outgoingmail_increment_number to False and outgoingmail_edit_irn to reply
        # => number incrementation because irn field is not editable
        api.portal.set_registry_record(
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_edit_irn",
            "reply",
        )
        reply.update()
        self.assertEqual(self.request["_hide_irn"], False)
        self.assertEqual(self.request["_auto_ref"], False)
        self.assertEqual(
            reply.widgets["internal_reference_no"].mode, "input"
        )  # not hidden
        self.assertEqual(reply.widgets["internal_reference_no"].value, "test-out/15")
        obj = reply.createAndAdd(self.om_params(reply))
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertEqual(om._auto_ref, False)
        self.assertEqual(
            api.portal.get_registry_record(
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"
            ),
            15,
        )  # No increment
        self.clean_request()

    def test_im_irn_conditions(self):
        self.assertEqual(
            [(t.value, translate(t.title)) for t in im_irn_conditions],
            [("show", "Always show"), ("hide", "Always hide")],
        )

    def test_om_irn_conditions(self):
        self.assertEqual(
            [(t.value, translate(t.title)) for t in om_irn_conditions],
            [
                ("show", "Always show"),
                ("hide", "Always hide"),
                ("reply", "Show only when replying"),
            ],
        )


class TestIDmsMailConfig(unittest.TestCase):

    layer = INTEGRATION

    def test_schema(self):
        self.assertEqual(
            [
                (f.__name__, f.label, f.fields)
                for f in IDmsMailConfig.queryTaggedValue(FIELDSETS_KEY)
            ],
            [
                (
                    "incomingmail",
                    "Incoming mail",
                    ["incomingmail_number", "incomingmail_talexpression"],
                ),
                (
                    "outgoingmail",
                    "Outgoing mail",
                    [
                        "outgoingmail_number",
                        "outgoingmail_talexpression",
                        "outgoingmail_edit_irn",
                        "outgoingmail_increment_number",
                        "outgoingmail_today_mail_date",
                    ],
                ),
            ],
        )
        self.assertEqual(
            IDmsMailConfig["outgoingmail_edit_irn"].vocabulary, om_irn_conditions
        )
        self.assertEqual(IDmsMailConfig["outgoingmail_edit_irn"].default, "show")
        self.assertTrue(IDmsMailConfig["outgoingmail_increment_number"].default)
        self.assertTrue(IDmsMailConfig["outgoingmail_today_mail_date"].default)
        for name in ("incomingmail_number", "outgoingmail_number"):
            self.assertIsNone(IDmsMailConfig[name].default)


class TestSettingsView(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.folder = api.content.create(
            container=self.portal, type="Folder", id="folder", title="Folder"
        )

    def test___call__(self):
        view = self.portal.restrictedTraverse("@@dmsmailcontent-settings")
        self.assertIsInstance(view, SettingsView)
        self.assertEqual(SettingsEditForm.schema, IDmsMailConfig)
        html = view()
        self.assertIn("Dms Mail settings", html)
        for fieldset, legend in (
            ("incomingmail", "Incoming mail"),
            ("outgoingmail", "Outgoing mail"),
        ):
            self.assertIn('id="fieldset-%s"' % fieldset, html)
            self.assertIn(legend, html)
        self.assertIn("value=\"python:'test-in/'+number\"", html)
        # saved in the registry
        set_form(
            self.request,
            {
                "form.widgets.incomingmail_number": "20",
                "form.widgets.incomingmail_talexpression": "python:'in/'+number",
                "form.widgets.outgoingmail_number": "30",
                "form.widgets.outgoingmail_talexpression": "python:'out/'+number",
                "form.widgets.outgoingmail_edit_irn": ["reply"],
                "form.widgets.outgoingmail_edit_irn-empty-marker": "1",
                "form.widgets.outgoingmail_increment_number-empty-marker": "1",
                "form.widgets.outgoingmail_today_mail_date-empty-marker": "1",
                "form.buttons.save": "Save",
            },
            "POST",
        )
        self.portal.restrictedTraverse("@@dmsmailcontent-settings")()
        self.assertEqual(api.portal.get_registry_record(IM_NUMBER), 20)
        self.assertEqual(
            api.portal.get_registry_record(OM_EXPRESSION), "python:'out/'+number"
        )
        self.assertEqual(api.portal.get_registry_record(OM_EDIT_IRN), "reply")
        self.assertFalse(api.portal.get_registry_record(OM_INCREMENT))
        self.assertFalse(api.portal.get_registry_record(OM_TODAY))
        # site setup permission
        setRoles(self.portal, TEST_USER_ID, ["Site Administrator"])
        self.assertIsInstance(
            self.portal.restrictedTraverse("@@dmsmailcontent-settings"), SettingsView
        )
        setRoles(self.portal, TEST_USER_ID, ["Contributor", "Editor", "Reviewer"])
        self.assertRaises(
            Unauthorized, self.portal.restrictedTraverse, "@@dmsmailcontent-settings"
        )

    def test_evaluateTalExpression(self):
        view = self.portal.restrictedTraverse("@@dmsmailcontent-settings")

        def evaluate(expression, number=5, **kwargs):
            return view.evaluateTalExpression(
                expression, self.folder, self.request, self.portal, number, **kwargs
            )

        # the number is a string
        self.assertEqual(evaluate("python:'in/' + number"), "in/5")
        self.assertEqual(evaluate("string:out/${number}"), "out/5")
        self.request["_irn"] = "in/1"
        self.assertEqual(
            evaluate(
                "python:'%s|%s|%s' % (context.getId(), portal.getId(), request['_irn'])"
            ),
            "folder|plone|in/1",
        )
        # restricted python
        self.assertIn("invalid attribute name", evaluate("python:tool.__name__"))
        self.assertEqual(evaluate("python:date.year()"), DateTime().year())
        self.assertEqual(evaluate("python:'%04d' % int(number)", number=12), "0012")
        # additional variables
        self.assertEqual(evaluate("python:prefix + number", prefix="S"), "S5")
        # an error is returned as text
        self.assertEqual(
            evaluate("python:unknown"),
            "Error in expression: name 'unknown' is not defined",
        )
