from collective.dms.mailcontent.browser.reply_form import ReplyForm
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.tests.base import clean_request
from collective.dms.mailcontent.tests.base import form_errors
from collective.dms.mailcontent.tests.base import OM_EDIT_IRN
from collective.dms.mailcontent.tests.base import OM_INCREMENT
from collective.dms.mailcontent.tests.base import OM_NUMBER
from collective.dms.mailcontent.tests.base import rel
from collective.dms.mailcontent.tests.base import set_form
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContent
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.i18n import translate
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import modified
from zope.security.management import endInteraction
from zope.security.management import newInteraction

import unittest


class TestReplyForm(unittest.TestCase):

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
        intids = getUtility(IIntIds)
        self.im = api.content.create(
            container=self.folder,
            type="dmsincomingmail",
            id="im",
            title="I mail",
            sender=[RelationValue(intids.getId(self.c1))],
            external_reference_no="xx/1",
            treating_groups=["Administrators"],
        )
        self.view = self.im.unrestrictedTraverse("@@reply")

    def reply_form(self, data=None, method="GET"):
        """A new reply form of the incoming mail, updated with the request data."""
        set_form(self.request, data, method)
        clean_request(self.request)
        view = self.im.restrictedTraverse("@@reply")
        view.update()
        return view

    def test_rf_label(self):
        self.assertEqual(translate(self.view.label), "Reply to test-in/10 - I mail")
        self.assertEqual(
            translate(self.view.label, target_language="fr"),
            "R\xe9pondre \xe0 test-in/10 - I mail",
        )

    def test___init__(self):
        self.assertIsInstance(self.view, ReplyForm)
        self.assertEqual(self.view.__name__, "reply")
        self.assertEqual(self.view.portal_type, "dmsoutgoingmail")
        self.assertTrue(self.view.reply_backrefs)
        # Plone 6: UIDs (Plone 4: linked_paths)
        self.assertIsNone(self.view.linked_uids)

    def test__get_linked_mails(self):
        im2 = api.content.create(
            container=self.folder, type="dmsincomingmail", id="im2", title="I mail 2"
        )
        om = api.content.create(
            container=self.folder, type="dmsoutgoingmail", id="om", title="O mail"
        )
        self.im.reply_to = [rel(im2), rel(om)]
        modified(self.im)
        om2 = api.content.create(
            container=self.folder, type="dmsoutgoingmail", id="om2", title="O mail 2"
        )
        # back references: om2 replies to the incoming mail, om too (listed once)
        for mail in (om2, om):
            mail.reply_to = [rel(self.im)]
            modified(mail)
        # Plone 6: the UIDs as the related items widget value (Plone 4: a tuple of paths)
        self.assertEqual(
            self.view._get_linked_mails(self.im),
            ";".join([m.UID() for m in (self.im, im2, om, om2)]),
        )
        # computed once
        self.im.reply_to = []
        self.assertEqual(self.view.linked_uids, self.view._get_linked_mails(self.im))
        self.assertEqual(len(self.view._get_linked_mails(self.im).split(";")), 4)
        # without back references
        view = ReplyForm(self.im, self.request)
        view.reply_backrefs = False
        self.assertEqual(view._get_linked_mails(self.im), self.im.UID())

    def test_update_fields_irn(self):
        for edit_irn, increment, hide, auto_ref in (
            ("show", True, False, None),
            ("show", False, False, False),
            ("reply", True, False, None),
            ("reply", False, False, False),
            ("hide", True, True, None),
            ("hide", False, True, None),
        ):
            api.portal.set_registry_record(OM_EDIT_IRN, edit_irn)
            api.portal.set_registry_record(OM_INCREMENT, increment)
            clean_request(self.request)
            self.view.update_fields_irn()
            self.assertEqual(self.request["_hide_irn"], hide, edit_irn)
            self.assertEqual(
                self.request.get("_auto_ref"), auto_ref, (edit_irn, increment)
            )

    def test_rf_updateFields(self):
        self.view.updateFields()
        # Plone 6: the UID (Plone 4: a tuple of paths); the contact widget keeps paths
        self.assertEqual(self.view.request["form.widgets.reply_to"], self.im.UID())
        self.assertEqual(
            self.view.request["form.widgets.recipients"], ("/plone/dir/imio",)
        )
        # the replied mail number, usable in the expression
        self.assertEqual(self.request["_irn"], "test-in/10")
        self.assertFalse(self.request["_hide_irn"])
        # submitted values are kept
        set_form(
            self.request,
            {
                "form.widgets.reply_to": ["/plone/folder"],
                "form.widgets.recipients": ["/plone"],
            },
        )
        view = ReplyForm(self.im, self.request)
        view.updateFields()
        self.assertEqual(self.request.form["form.widgets.reply_to"], ["/plone/folder"])
        self.assertEqual(self.request.form["form.widgets.recipients"], ["/plone"])
        # masterselect ajax call: nothing completed
        set_form(self.request)
        self.request["masterID"] = "form-widgets-sender"
        ReplyForm(self.im, self.request).updateFields()
        self.assertNotIn("form.widgets.reply_to", self.request.form)
        self.assertNotIn("form.widgets.recipients", self.request.form)
        del self.request.other["masterID"]
        # an incoming mail without sender (created by a script): no recipient
        # Plone 6: fixed (Plone 4 bug: TypeError)
        self.im.sender = None
        ReplyForm(self.im, self.request).updateFields()
        self.assertEqual(self.request.form["form.widgets.recipients"], ())

    def test_rf_updateWidgets(self):
        self.view.update()
        self.assertEqual(self.view.widgets["IDublinCore.title"].value, "I mail")
        self.assertEqual(self.view.widgets["treating_groups"].value, ["Administrators"])
        # Plone 6: the UID (Plone 4: a tuple of paths)
        self.assertEqual(self.view.widgets["reply_to"].value, self.im.UID())
        self.assertEqual(self.view.widgets["recipients"].value, ("/plone/dir/imio",))
        self.assertEqual(self.view.widgets["external_reference_no"].value, "xx/1")
        self.assertEqual(self.view.widgets["recipient_groups"].value, ())
        self.assertEqual(
            self.view.widgets["internal_reference_no"].value, "test-out/10"
        )
        self.assertEqual(self.view.widgets["internal_reference_no"].mode, "input")
        # rendered: the incoming mail in the related items input, its sender checked
        html = self.view.widgets["reply_to"].render()
        self.assertIn('value="%s"' % self.im.UID(), html)
        self.assertIn("test-in/10 - I mail", html)
        self.assertIn(
            'value="/plone/dir/imio" checked="checked"',
            self.view.widgets["recipients"].render(),
        )
        # the recipient groups of the incoming mail
        self.im.recipient_groups = ["Reviewers"]
        self.assertEqual(
            self.reply_form().widgets["recipient_groups"].value, ["Reviewers"]
        )
        # the internal reference is hidden and emptied for a non manager when the setting hides it
        api.portal.set_registry_record(OM_EDIT_IRN, "hide")
        view = self.reply_form()
        self.assertEqual(view.widgets["internal_reference_no"].mode, "hidden")
        self.assertEqual(view.widgets["internal_reference_no"].value, "")
        # masterselect ajax call: no relation completed
        set_form(self.request)
        self.request["masterID"] = "form-widgets-sender"
        view = ReplyForm(self.im, self.request)
        view.update()
        self.assertEqual(view.widgets["IDublinCore.title"].value, "I mail")
        self.assertIsNone(
            view.widgets["reply_to"].value
        )  # Plone 6: empty related items widget (Plone 4: ())
        self.assertEqual(view.widgets["recipients"].value, ())
        del self.request.other["masterID"]
        # an incoming mail without sender (created by a script): no recipient
        # Plone 6: fixed (Plone 4 bug: TypeError)
        self.im.sender = None
        self.assertEqual(self.reply_form().widgets["recipients"].value, ())

    def test_add_content(self):
        obj = createContent("dmsoutgoingmail", title="Reply")
        container, new_object = self.view.add_content(obj)
        # created next to the incoming mail
        self.assertEqual(container, self.folder)
        self.assertEqual(new_object.aq_parent, self.folder)
        self.assertEqual(new_object.title, "Reply")

    def test_rf_add(self):
        setRoles(self.portal, TEST_USER_ID, ["Member", "Manager"])
        self.view.update()
        params = {
            "IDublinCore.title": self.view.widgets["IDublinCore.title"].value,
            "treating_groups": ["Administrators"],
            "internal_reference_no": self.view.widgets["internal_reference_no"].value,
            "reply_to": [self.im],
            "recipient_groups": [],
        }
        self.assertEqual(len(self.folder.objectIds()), 1)
        obj = self.view.createAndAdd(params)
        self.assertEqual(len(self.folder.objectIds()), 2)
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertListEqual(om.recipient_groups, [])
        # treating group is different from im
        params["treating_groups"] = ["Reviewers"]
        obj = self.view.createAndAdd(params)
        self.assertEqual(len(self.folder.objectIds()), 3)
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertListEqual(om.recipient_groups, ["Administrators"])
        # a response, then redirected to its view
        self.assertTrue(om._is_response)
        self.assertEqual(self.view.immediate_view, "%s/view" % om.absolute_url())
        # the added group is indexed
        # Plone 6: fixed (Plone 4 bug: add() reindexed the unwrapped object, no catalog found, nothing indexed)
        self.assertEqual(
            [
                b.getObject()
                for b in api.content.find(recipient_groups="Administrators")
            ],
            [om],
        )
        # single treating groups (as imio.dms.mail), without immediate view
        self.im.treating_groups = "Administrators"
        params.update({"treating_groups": "Reviewers", "recipient_groups": None})
        self.portal.portal_types.dmsoutgoingmail.immediate_view = ""
        obj = self.view.createAndAdd(params)
        om = api.content.find(self.folder, id=obj.id)[0].getObject()
        self.assertListEqual(om.recipient_groups, ["Administrators"])
        self.assertEqual(self.view.immediate_view, om.absolute_url())
        # no number increment asked by the irn settings
        self.request["_auto_ref"] = False
        number = api.portal.get_registry_record(OM_NUMBER)
        obj = self.view.createAndAdd(params)
        self.assertFalse(
            api.content.find(self.folder, id=obj.id)[0].getObject()._auto_ref
        )
        self.assertEqual(api.portal.get_registry_record(OM_NUMBER), number)
        # the user replies to the incoming mail with the form: the outgoing mail is created next to it
        newInteraction()
        self.addCleanup(endInteraction)
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        im2 = api.content.create(
            container=self.folder, type="dmsincomingmail", id="im2", title="I mail 2"
        )
        self.im.reply_to = [rel(im2)]
        modified(self.im)
        data = {
            "form.widgets.IDublinCore.title": "Re: I mail",
            "form.widgets.treating_groups": ["Reviewers"],
            "form.widgets.recipient_groups-empty-marker": "1",
            "form.buttons.save": "Save",
        }
        view = self.reply_form(data, "POST")
        self.assertEqual(form_errors(view), {})
        # a submitted value is kept
        self.assertEqual(view.widgets["IDublinCore.title"].value, "Re: I mail")
        om = self.folder["re-i-mail"]
        self.assertEqual(view.immediate_view, "http://nohost/plone/folder/re-i-mail")
        self.assertEqual(om.portal_type, "dmsoutgoingmail")
        self.assertEqual(om.internal_reference_no, "test-out/%d" % number)
        # the replied mails (the validator accepted the incoming mail itself): the incoming mail, its links and
        # its back references (the previous replies), and its senders
        self.assertEqual(
            [r.to_object.getId() for r in om.reply_to],
            ["im", "im2", "i-mail", "i-mail-1", "i-mail-2", "i-mail-3"],
        )
        self.assertEqual([r.to_object for r in om.recipients], [self.c1])
        self.assertEqual(om.get_replied(first=False), [self.im, im2])
        self.assertEqual(om.treating_groups, ["Reviewers"])
        self.assertTrue(om._is_response)
        # the treating groups of the replied mails (incoming and outgoing) are added to the recipient groups, once
        # Plone 6: fixed (Plone 4 bug: None for im2 without treating group, Administrators twice: im and a reply)
        self.assertEqual(om.recipient_groups, ["Administrators"])
