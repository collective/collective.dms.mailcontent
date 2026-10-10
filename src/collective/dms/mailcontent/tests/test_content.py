# -*- coding: utf8 -*-
"""dmsmail.py"""
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.contact.widget.widgets import ContactAutocompleteMultiSelectionWidget
from collective.contact.widget.widgets import ContactAutocompleteSelectionWidget
from collective.dms.basecontent.dmsdocument import IDmsDocument
from collective.dms.basecontent.relateddocs import RelatedDocsWidget
from collective.dms.mailcontent import dmsmail
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent.tests.base import create_contacts
from collective.dms.mailcontent.tests.base import form_errors
from collective.dms.mailcontent.tests.base import IM_EXPRESSION
from collective.dms.mailcontent.tests.base import IM_NUMBER
from collective.dms.mailcontent.tests.base import OM_NUMBER
from collective.dms.mailcontent.tests.base import OM_TODAY
from collective.dms.mailcontent.tests.base import rel
from collective.dms.mailcontent.tests.base import set_form
from imio.helpers.emailer import InvalidEmailAddress
from plone import api
from plone.app.dexterity.textindexer.indexer import dynamic_searchable_text_indexer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield import RichText
from plone.app.textfield.widget import RichTextWidget
from plone.app.z3cform.widgets.datetime import DatetimeWidget
from plone.app.z3cform.widgets.datetime import DateWidget
from plone.app.z3cform.widgets.text import TextWidget
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.schema import SCHEMA_CACHE
from plone.dexterity.utils import addContentToContainer
from plone.dexterity.utils import createContent
from plone.dexterity.utils import createContentInContainer
from plone.registry.interfaces import IRegistry
from plone.supermodel.interfaces import ISchemaPolicy
from z3c.form.browser.checkbox import CheckBoxWidget
from z3c.form.interfaces import IValidator
from z3c.relationfield import RelationList
from zope.component import getGlobalSiteManager
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import Invalid
from zope.lifecycleevent import modified
from zope.publisher.base import TestRequest
from zope.schema.interfaces import RequiredMissing
from zope.security.management import endInteraction
from zope.security.management import newInteraction

import datetime
import unittest


IM_FIELDS = [
    "IDublinCore.title",
    "IDublinCore.description",
    "sender",
    "recipients",
    "original_mail_date",
    "reception_date",
    "internal_reference_no",
    "external_reference_no",
    "reply_to",
    "treating_groups",
    "recipient_groups",
    "related_docs",
    "notes",
]
OM_FIELDS = IM_FIELDS[:4] + ["mail_date"] + IM_FIELDS[6:]
EMAIL_FIELDS = [
    "email_status",
    "email_subject",
    "email_sender",
    "email_recipient",
    "email_cc",
    "email_bcc",
    "email_attachments",
    "email_body",
]
TODAY = datetime.date.today()


class TestContentTypes(unittest.TestCase):
    """Base class to test new content types"""

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        # the publisher opens a security interaction, needed by the relation widgets
        newInteraction()
        self.addCleanup(endInteraction)
        # Plone 6: the text indexer of plone.app.dexterity is registered below the layer, where the SearchableText
        # indexer of collective.dms.basecontent wins whatever the behaviors; registered here as in a real instance
        gsm = getGlobalSiteManager()
        gsm.registerAdapter(dynamic_searchable_text_indexer, name="SearchableText")
        self.addCleanup(gsm.unregisterAdapter, dynamic_searchable_text_indexer, name="SearchableText")
        self.folder = api.content.create(container=self.portal, type="Folder", id="folder", title="Folder")

    def add_form(self, portal_type, data=None, method="GET"):
        """The add form of portal_type, updated with the request data."""
        set_form(self.request, data, method)
        form = self.folder.restrictedTraverse("++add++%s" % portal_type).form_instance
        form.update()
        return form

    def edit_form(self, obj, data=None, view_name="@@edit", method="POST"):
        set_form(self.request, data, method)
        form = obj.restrictedTraverse(view_name)
        form = getattr(form, "form_instance", form)
        form.update()
        return form


class TestDmsmailMethods(TestContentTypes):
    """Module functions"""

    def test_reception_date_default_value(self):
        reception_date = dmsmail.receptionDateDefaultValue("")
        current_date = datetime.datetime.now()
        self.assertEqual(reception_date.date(), current_date.date())
        self.assertEqual(reception_date.hour, current_date.hour)
        self.assertEqual(reception_date.minute, current_date.minute)
        # the add form proposes now
        # Plone 6: datetime-local value of plone.app.z3cform, to the minute (Plone 4: a tuple), no timezone
        value = self.add_form("dmsincomingmail").widgets["reception_date"].value
        proposed = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M")
        self.assertLess(abs(proposed - datetime.datetime.now()), datetime.timedelta(minutes=2))
        # Plone 4: a default_value is only used by the add form, an object created without value has none
        im = api.content.create(container=self.folder, type="dmsincomingmail", id="im", title="I mail")
        self.assertIsNone(im.reception_date)
        # nor the edit form (an emptied date stays empty)
        self.assertEqual(self.edit_form(im, method="GET").widgets["reception_date"].value, "")

    def test_original_date_default_value(self):
        self.assertEqual(dmsmail.originalMailDateDefaultValue(""), datetime.date.today() - datetime.timedelta(3))
        # the add form proposes 3 days ago
        three_days_ago = TODAY - datetime.timedelta(days=3)
        # Plone 6: ISO date value of plone.app.z3cform (Plone 4: a tuple)
        self.assertEqual(
            self.add_form("dmsincomingmail").widgets["original_mail_date"].value, three_days_ago.isoformat()
        )
        # Plone 4: a default_value is only used by the add form
        im = api.content.create(container=self.folder, type="dmsincomingmail", id="im", title="I mail")
        self.assertIsNone(im.original_mail_date)
        self.assertEqual(self.edit_form(im, method="GET").widgets["original_mail_date"].value, "")

    def test_mailDateDefaultValue(self):
        self.assertEqual(dmsmail.mailDateDefaultValue(None), TODAY)
        # Plone 6: ISO date value of plone.app.z3cform (Plone 4: a tuple)
        self.assertEqual(self.add_form("dmsoutgoingmail").widgets["mail_date"].value, TODAY.isoformat())
        # Plone 4: a default_value is only used by the add form
        om = api.content.create(container=self.folder, type="dmsoutgoingmail", id="om", title="O mail")
        self.assertIsNone(om.mail_date)
        self.assertEqual(
            self.edit_form(om, view_name="@@dmsdocument-edit", method="GET").widgets["mail_date"].value, ""
        )
        # no default date when the setting is off
        api.portal.set_registry_record(OM_TODAY, False)
        self.assertIsNone(dmsmail.mailDateDefaultValue(None))
        self.assertEqual(self.add_form("dmsoutgoingmail").widgets["mail_date"].value, "")

    def test_validateIndexValueUniqueness(self):
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        # test with container as context, value doesn't exist
        self.assertEqual(
            dmsmail.validateIndexValueUniqueness(
                self.portal, dmsmail.IDmsIncomingMail, "internal_reference_number", "54321"
            ),
            None,
        )
        # test with container as context, value exists
        with self.assertRaises(Invalid) as cm:
            dmsmail.validateIndexValueUniqueness(
                self.portal, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345"
            )
        self.assertEqual(cm.exception.args[0], "This value is already used")
        # test with object as context, value doesn't exist
        self.assertEqual(
            dmsmail.validateIndexValueUniqueness(
                imail1, dmsmail.IDmsIncomingMail, "internal_reference_number", "54321"
            ),
            None,
        )
        # test with object as context, value exists on the same object
        self.assertEqual(
            dmsmail.validateIndexValueUniqueness(
                imail1, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345"
            ),
            None,
        )
        # test with object as context and a sub element in the folder, value exists on the same object
        createContentInContainer(imail1, "dmsmainfile", **{"title": "File 1"})
        self.assertEqual(
            dmsmail.validateIndexValueUniqueness(
                imail1, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345"
            ),
            None,
        )
        # test with object as context, value exists on a different object too
        imail2 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 2"}
        )
        with self.assertRaises(Invalid) as cm:
            dmsmail.validateIndexValueUniqueness(imail2, dmsmail.IDmsIncomingMail, "internal_reference_number", "12345")
        self.assertEqual(cm.exception.args[0], "This value is already used")
        # test with empty value
        imail3 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "", "title": "Test 2"}
        )
        self.assertEqual(
            dmsmail.validateIndexValueUniqueness(
                self.portal, dmsmail.IDmsIncomingMail, "internal_reference_number", ""
            ),
            None,
        )
        self.assertEqual(
            dmsmail.validateIndexValueUniqueness(imail3, dmsmail.IDmsIncomingMail, "internal_reference_number", ""),
            None,
        )
        # the index is shared: an outgoing mail number is refused for an incoming mail
        createContentInContainer(self.portal, "dmsoutgoingmail", **{"internal_reference_no": "999", "title": "O"})
        self.assertRaises(
            Invalid,
            dmsmail.validateIndexValueUniqueness,
            self.portal,
            dmsmail.IDmsIncomingMail,
            "internal_reference_number",
            "999",
        )

    def test_evaluateInternalReference(self):
        self.assertEqual(
            dmsmail.evaluateInternalReference(
                self.portal,
                self.portal.REQUEST,
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number",
                "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_talexpression",
            ),
            "test-in/10",
        )
        # the number defaults to 1
        api.portal.set_registry_record(IM_NUMBER, 0)
        self.assertEqual(
            dmsmail.evaluateInternalReference(self.folder, self.request, IM_NUMBER, IM_EXPRESSION), "test-in/1"
        )
        # the expression gets the context and the request
        api.portal.set_registry_record(IM_EXPRESSION, "python:context.getId() + '/' + request.get('_irn', number)")
        self.assertEqual(
            dmsmail.evaluateInternalReference(self.folder, self.request, IM_NUMBER, IM_EXPRESSION), "folder/1"
        )
        self.request["_irn"] = "in/5"
        self.assertEqual(
            dmsmail.evaluateInternalReference(self.folder, self.request, IM_NUMBER, IM_EXPRESSION), "folder/in/5"
        )
        # an error in the expression is returned
        api.portal.set_registry_record(IM_EXPRESSION, "python:unknown")
        self.assertEqual(
            dmsmail.evaluateInternalReference(self.folder, self.request, IM_NUMBER, IM_EXPRESSION),
            "Error in expression: name 'unknown' is not defined",
        )
        # without a browser request (no view)
        self.assertEqual(
            dmsmail.evaluateInternalReference(self.folder, TestRequest("/"), IM_NUMBER, IM_EXPRESSION),
            "Error getting view...",
        )

    def test_internalReferenceIncomingMailDefaultValue(self):
        # the add form proposes the next number, as text
        value = self.add_form("dmsincomingmail").widgets["internal_reference_no"].value
        self.assertEqual(value, "test-in/10")
        self.assertIsInstance(value, type(""))
        api.portal.set_registry_record(IM_NUMBER, 12)
        self.assertEqual(self.add_form("dmsincomingmail").widgets["internal_reference_no"].value, "test-in/12")
        # the edit form shows the stored value
        im = api.content.create(
            container=self.folder, type="dmsincomingmail", id="im", title="I mail", internal_reference_no="E1"
        )
        self.assertEqual(self.edit_form(im, method="GET").widgets["internal_reference_no"].value, "E1")

    def test_internalReferenceOutgoingMailDefaultValue(self):
        value = self.add_form("dmsoutgoingmail").widgets["internal_reference_no"].value
        self.assertEqual(value, "test-out/10")
        self.assertIsInstance(value, type(""))
        api.portal.set_registry_record(OM_NUMBER, 12)
        self.assertEqual(self.add_form("dmsoutgoingmail").widgets["internal_reference_no"].value, "test-out/12")

    def test_incrementIncomingMailNumber(self):
        registry = getUtility(IRegistry)
        old_value = registry["collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number"]
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        self.assertEqual(
            registry["collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number"], old_value + 1
        )
        self.assertEqual(imail1.internal_reference_no, "12345")
        # we create a dmsincomingmail without internal_reference_no, it will be generated
        imail2 = createContentInContainer(self.portal, "dmsincomingmail", **{"title": "Test 2"})
        self.assertEqual(imail2.internal_reference_no, "test-in/11")
        self.assertEqual(registry[IM_NUMBER], 12)
        # Plone 6: the forced value is a text, accepted by the field (Plone 4 bug: bytes string, fixed by Python 3)
        dmsmail.IDmsIncomingMail["internal_reference_no"].bind(imail2).validate(imail2.internal_reference_no)
        # the forced value is indexed
        brains = self.portal.portal_catalog(internal_reference_number="test-in/11")
        self.assertEqual([b.getObject() for b in brains], [imail2])
        self.assertEqual(brains[0].Title, "test-in/11 - Test 2")
        self.assertEqual(len(self.portal.portal_catalog(SearchableText="test-in/11")), 1)
        # an empty value is forced too
        imail3 = createContentInContainer(self.portal, "dmsincomingmail", title="Test 3", internal_reference_no="")
        self.assertEqual(imail3.internal_reference_no, "test-in/12")
        # only on creation
        imail3.internal_reference_no = None
        modified(imail3)
        self.assertIsNone(imail3.internal_reference_no)
        self.assertEqual(registry[IM_NUMBER], 13)

    def test_incrementOutgoingMailNumber(self):
        omail1 = createContentInContainer(self.folder, "dmsoutgoingmail", title="Test 1", internal_reference_no="O1")
        self.assertEqual(omail1.internal_reference_no, "O1")
        self.assertEqual(api.portal.get_registry_record(OM_NUMBER), 11)
        # without value, the number is generated and indexed
        omail2 = createContentInContainer(self.folder, "dmsoutgoingmail", title="Test 2")
        self.assertEqual(omail2.internal_reference_no, "test-out/11")
        self.assertEqual(api.portal.get_registry_record(OM_NUMBER), 12)
        brains = self.portal.portal_catalog(internal_reference_number="test-out/11")
        self.assertEqual([b.getObject() for b in brains], [omail2])
        self.assertEqual(brains[0].Title, "test-out/11 - Test 2")
        # a mail marked _auto_ref = False (by the forms) does not increment the number
        omail3 = createContent("dmsoutgoingmail", title="Test 3")
        omail3._auto_ref = False
        omail3 = addContentToContainer(self.folder, omail3)
        self.assertEqual(omail3.internal_reference_no, "test-out/12")
        self.assertEqual(api.portal.get_registry_record(OM_NUMBER), 12)

    def test_indexes(self):
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        # get brain
        brains = self.portal.portal_catalog(path="/".join(imail1.getPhysicalPath()))
        self.assertEqual(len(brains), 1)
        self.assertEqual(imail1, brains[0].getObject())
        # search by title
        brains = self.portal.portal_catalog(Title="12345")
        self.assertEqual(len(brains), 1)
        self.assertEqual(imail1, brains[0].getObject())
        # search by SearchableText (textindexer.searchable on internal_reference_no)
        brains = self.portal.portal_catalog(SearchableText="12345")
        self.assertEqual([b.getObject() for b in brains], [imail1])
        # Plone 6: the outgoing mail type has the text indexer behavior too, its number is searchable
        # (Plone 4: no text indexer behavior, number not searchable)
        omail = createContentInContainer(self.portal, "dmsoutgoingmail", internal_reference_no="54321", title="Out")
        self.assertEqual([b.getObject() for b in self.portal.portal_catalog(SearchableText="54321")], [omail])
        self.assertEqual([b.getObject() for b in self.portal.portal_catalog(SearchableText="Out")], [omail])


class TestInternalReferenceBaseValidator(TestContentTypes):
    def test_good_value(self):
        form = self.add_form("dmsincomingmail")
        widget = form.widgets["internal_reference_no"]
        validator = dmsmail.InternalReferenceBaseValidator(self.folder, self.request, form, widget.field, widget)
        self.assertEqual(validator.good_value(), "")

    def test_validate(self):
        im = api.content.create(container=self.folder, type="dmsincomingmail", id="im", title="I mail")
        im2 = api.content.create(container=self.folder, type="dmsincomingmail", id="im2", title="I mail 2")
        om = api.content.create(container=self.folder, type="dmsoutgoingmail", id="om", title="O mail")
        data = {
            "form.widgets.IDublinCore.title": "Mail",
            "form.widgets.reply_to": "",
            "form.buttons.save": "Save",
        }
        # add: a used value is refused, the next number is proposed (sender is required and not given)
        data["form.widgets.internal_reference_no"] = "test-in/10"
        errors = form_errors(self.add_form("dmsincomingmail", data, "POST"))
        self.assertEqual(
            errors,
            {
                "sender": "Required input is missing.",
                "internal_reference_no": "This value is already used. A good value would be: test-in/12",
            },
        )
        # an outgoing mail number too
        data["form.widgets.internal_reference_no"] = "test-out/10"
        self.assertIn("internal_reference_no", form_errors(self.add_form("dmsincomingmail", data, "POST")))
        # a new or an empty value is accepted
        for value in ("test-in/12", ""):
            data["form.widgets.internal_reference_no"] = value
            self.assertEqual(list(form_errors(self.add_form("dmsincomingmail", data, "POST"))), ["sender"])
        # edit: its own value is accepted, the value of another mail is refused
        data["form.widgets.internal_reference_no"] = "test-in/10"
        self.assertEqual(list(form_errors(self.edit_form(im, data))), ["sender"])
        self.assertEqual(
            form_errors(self.edit_form(im2, data))["internal_reference_no"],
            "This value is already used. A good value would be: test-in/12",
        )
        # outgoing mail add and edit forms (recipients is required and not given)
        data["form.widgets.internal_reference_no"] = "test-out/10"
        self.assertEqual(
            form_errors(self.add_form("dmsoutgoingmail", data, "POST")),
            {
                "recipients": "Required input is missing.",
                "internal_reference_no": "This value is already used. A good value would be: test-out/11",
            },
        )
        self.assertEqual(list(form_errors(self.edit_form(om, data, "@@dmsdocument-edit"))), ["recipients"])
        self.assertIn("internal_reference_no", form_errors(self.edit_form(im, data)))


class TestInternalReferenceIncomingMailValidator(TestContentTypes):
    def test_good_value(self):
        form = self.add_form("dmsincomingmail")
        widget = form.widgets["internal_reference_no"]
        validator = getMultiAdapter((self.folder, self.request, form, widget.field, widget), IValidator)
        self.assertIsInstance(validator, dmsmail.InternalReferenceIncomingMailValidator)
        self.assertEqual(validator.good_value(), "test-in/10")
        api.content.create(container=self.folder, type="dmsincomingmail", id="im", title="I mail")
        self.assertEqual(validator.good_value(), "test-in/11")


class TestInternalReferenceOutgoingMailValidator(TestContentTypes):
    def test_good_value(self):
        form = self.add_form("dmsoutgoingmail")
        widget = form.widgets["internal_reference_no"]
        validator = getMultiAdapter((self.folder, self.request, form, widget.field, widget), IValidator)
        self.assertIsInstance(validator, dmsmail.InternalReferenceOutgoingMailValidator)
        self.assertEqual(validator.good_value(), "test-out/10")
        api.content.create(container=self.folder, type="dmsoutgoingmail", id="om", title="O mail")
        self.assertEqual(validator.good_value(), "test-out/11")


class TestReplyToValidator(TestContentTypes):
    def test_validate(self):
        sender = create_contacts(self.portal)
        im = api.content.create(
            container=self.folder, type="dmsincomingmail", id="im", title="I mail", sender=[rel(sender)]
        )
        im2 = api.content.create(container=self.folder, type="dmsincomingmail", id="im2", title="I mail 2")
        om = api.content.create(container=self.folder, type="dmsoutgoingmail", id="om", title="O mail")
        message = "You cannot choose the current object as a reply to."
        data = {"form.widgets.IDublinCore.title": "Mail", "form.buttons.save": "Save"}
        # the mail itself is refused
        # Plone 6: the related items widget sends UIDs separated by ";" (Plone 4: a list of paths)
        data["form.widgets.reply_to"] = "%s;%s" % (im.UID(), im2.UID())
        self.assertEqual(form_errors(self.edit_form(im, data))["reply_to"], message)
        data["form.widgets.reply_to"] = om.UID()
        self.assertEqual(form_errors(self.edit_form(om, data, "@@dmsdocument-edit"))["reply_to"], message)
        # other mails are accepted
        self.assertNotIn("reply_to", form_errors(self.edit_form(im, data)))
        data["form.widgets.reply_to"] = im.UID()
        self.assertNotIn("reply_to", form_errors(self.edit_form(om, data, "@@dmsdocument-edit")))
        self.assertNotIn("reply_to", form_errors(self.add_form("dmsoutgoingmail", data, "POST")))
        # an empty value, as the browser sends it
        data["form.widgets.reply_to"] = ""
        self.assertNotIn("reply_to", form_errors(self.edit_form(im, data)))
        # without value (missing widget)
        # Plone 6: accepted (Plone 4 bug: TypeError, "self.context in value or []" tested None; fixed on the branch)
        del data["form.widgets.reply_to"]
        self.assertNotIn("reply_to", form_errors(self.edit_form(im, data)))
        # the validator of each type
        form = self.edit_form(im, method="GET")
        widget = form.widgets["reply_to"]
        validator = getMultiAdapter((im, self.request, form, widget.field, widget), IValidator)
        self.assertIsInstance(validator, dmsmail.IMReplyToValidator)
        self.assertRaises(Invalid, validator.validate, [im])
        # skipped in the reply form: the replied incoming mail is the context and is in the value
        reply = im.restrictedTraverse("@@reply")
        set_form(self.request)
        reply.update()
        widget = reply.widgets["reply_to"]
        validator = getMultiAdapter((im, self.request, reply, widget.field, widget), IValidator)
        self.assertIsInstance(validator, dmsmail.OMReplyToValidator)
        self.assertIsNone(validator.validate([im]))


class TestDmsIncomingMail(TestContentTypes):
    def test_Title(self):
        imail1 = createContentInContainer(
            self.portal, "dmsincomingmail", **{"internal_reference_no": "12345", "title": "Test 1"}
        )
        self.assertEqual(imail1.Title(), "12345 - Test 1")
        imail1.internal_reference_no = None
        self.assertEqual(imail1.Title(), "Test 1")
        # Plone 6: a text (Plone 4: utf8 encoded)
        imail1.title = "R\xe9ponse"
        imail1.internal_reference_no = "in/\xe9"
        self.assertEqual(imail1.Title(), "in/\xe9 - R\xe9ponse")


class TestDmsOutgoingMail(TestContentTypes):
    def test_Title(self):
        omail = createContentInContainer(self.folder, "dmsoutgoingmail", title="Test 1", internal_reference_no="O1")
        self.assertEqual(omail.Title(), "O1 - Test 1")
        omail.internal_reference_no = None
        self.assertEqual(omail.Title(), "Test 1")
        # Plone 6: a text (Plone 4: utf8 encoded)
        omail.title = "R\xe9ponse"
        self.assertEqual(omail.Title(), "R\xe9ponse")

    def test_get_replied(self):
        imail1 = createContentInContainer(self.folder, "dmsincomingmail", **{"title": "In 1"})
        imail2 = createContentInContainer(self.folder, "dmsincomingmail", **{"title": "In 2"})
        omail1 = createContentInContainer(self.folder, "dmsoutgoingmail", **{"title": "Out 1"})
        omail2 = createContentInContainer(self.folder, "dmsoutgoingmail", **{"title": "Out 2"})
        self.assertEqual(omail1.get_replied(), None)
        self.assertEqual(omail1.get_replied(first=False), [])
        omail1.reply_to = [rel(imail1)]
        modified(omail1)
        self.assertEqual(omail1.get_replied(), imail1)
        omail1.reply_to = [rel(imail2), rel(imail1)]
        modified(omail1)
        self.assertEqual(omail1.get_replied(), imail2)
        self.assertListEqual(omail1.get_replied(first=False), [imail2, imail1])
        imail2.reply_to = [rel(omail2)]
        modified(imail2)
        self.assertEqual(omail2.get_replied(), imail2)
        omail2.reply_to = [rel(omail1)]
        modified(omail2)
        self.assertEqual(omail2.get_replied(), imail2)
        self.assertEqual(omail2.get_replied(intf=IDmsDocument), omail1)
        self.assertEqual(omail2.get_replied(first=False, intf=IDmsDocument), [omail1, imail2])
        # a back reference of another type is filtered too: an outgoing mail replying to an outgoing mail
        omail3 = createContentInContainer(self.folder, "dmsoutgoingmail", **{"title": "Out 3"})
        omail4 = createContentInContainer(self.folder, "dmsoutgoingmail", **{"title": "Out 4"})
        omail4.reply_to = [rel(omail3)]
        modified(omail4)
        self.assertIsNone(omail3.get_replied())
        self.assertEqual(omail3.get_replied(first=False), [])
        self.assertEqual(omail3.get_replied(first=False, intf=IDmsDocument), [omail4])
        # a mail both in the references and in the back references is listed once
        omail2.reply_to = [rel(imail2), rel(imail1)]
        modified(omail2)
        self.assertEqual(omail2.get_replied(first=False), [imail2, imail1])


class TestDmsIncomingMailSchemaPolicy(TestContentTypes):
    def test_bases(self):
        policy = getUtility(ISchemaPolicy, name="schema_policy_dmsincomingmail")
        self.assertIsInstance(policy, dmsmail.DmsIncomingMailSchemaPolicy)
        self.assertEqual(policy.bases("dmsincomingmail", None), (dmsmail.IDmsIncomingMail,))
        schema = getUtility(IDexterityFTI, name="dmsincomingmail").lookupSchema()
        self.assertTrue(schema.isOrExtends(dmsmail.IDmsIncomingMail))
        self.assertTrue(schema.isOrExtends(IDmsDocument))


class TestDmsOutgoingMailSchemaPolicy(TestContentTypes):
    def test_bases(self):
        policy = getUtility(ISchemaPolicy, name="schema_policy_dmsoutgoingmail")
        self.assertIsInstance(policy, dmsmail.DmsOutgoingMailSchemaPolicy)
        self.assertEqual(policy.bases("dmsoutgoingmail", None), (dmsmail.IDmsOutgoingMail,))
        schema = getUtility(IDexterityFTI, name="dmsoutgoingmail").lookupSchema()
        self.assertTrue(schema.isOrExtends(dmsmail.IDmsOutgoingMail))
        self.assertFalse(schema.isOrExtends(dmsmail.IDmsIncomingMail))


class MailSchemaTestCase(TestContentTypes):
    def check_reply_to(self, field):
        # Plone 6: a RelationList of a CatalogSource, the widget shows the back references (Plone 4: RelatedDocs
        # field with display_backrefs)
        self.assertIsInstance(field, RelationList)
        self.assertFalse(field.required)
        self.assertEqual(
            field.value_type.source.query,
            {
                "object_provides": (
                    "collective.dms.mailcontent.dmsmail.IDmsIncomingMail",
                    "collective.dms.mailcontent.dmsmail.IDmsOutgoingMail",
                )
            },
        )

    def reply_to_tuples(self, obj):
        """The reply_to links of the mail view."""
        set_form(self.request)
        view = obj.restrictedTraverse("@@view")
        view.update()
        # Plone 6: a method of basecontent's RelatedDocsWidget (Plone 4: a property)
        return view.widgets["reply_to"].tuples()


class TestIDmsIncomingMail(MailSchemaTestCase):
    def test_schema(self):
        schema = dmsmail.IDmsIncomingMail
        self.assertTrue(schema.isOrExtends(IDmsDocument))
        self.assertIsInstance(schema["sender"], ContactList)
        self.assertTrue(schema["sender"].required)
        self.assertIsInstance(schema["recipients"], ContactList)
        self.assertFalse(schema["recipients"].required)
        self.assertEqual(schema["original_mail_date"].min, datetime.date(1990, 1, 1))
        # computed at the start of the instance
        self.assertEqual(schema["original_mail_date"].max, TODAY + datetime.timedelta(days=7))
        self.assertEqual(schema["reception_date"].min, datetime.datetime(1990, 1, 1))
        self.assertEqual(schema["reception_date"].max.date(), TODAY + datetime.timedelta(days=7))
        for name in ("original_mail_date", "reception_date", "external_reference_no", "internal_reference_no"):
            self.assertFalse(schema[name].required)
        self.check_reply_to(schema["reply_to"])
        # the add form: order and widgets
        form = self.add_form("dmsincomingmail")
        self.assertEqual(list(form.widgets.keys()), IM_FIELDS)
        self.assertIsInstance(form.widgets["sender"], ContactAutocompleteMultiSelectionWidget)
        self.assertIsInstance(form.widgets["recipients"], ContactAutocompleteMultiSelectionWidget)
        self.assertIsInstance(form.widgets["original_mail_date"], DateWidget)
        # Plone 6: plone.app.z3cform widgets, the datetime-local input always has the time (Plone 4: show_time)
        self.assertIsInstance(form.widgets["reception_date"], DatetimeWidget)
        # Plone 6: the text widget of plone.app.z3cform (Plone 4: of z3c.form)
        self.assertIsInstance(form.widgets["internal_reference_no"], TextWidget)
        self.assertIsInstance(form.widgets["reply_to"], RelatedDocsWidget)
        # a date out of the bounds is refused
        data = {
            "form.widgets.IDublinCore.title": "Mail",
            # Plone 6: one ISO date input (Plone 4: day, month and year inputs)
            "form.widgets.original_mail_date": "1989-12-31",
            "form.widgets.reply_to": "",
            "form.buttons.save": "Save",
        }
        self.assertIn("original_mail_date", form_errors(self.add_form("dmsincomingmail", data, "POST")))

    def test_reply_to(self):
        im = api.content.create(container=self.folder, type="dmsincomingmail", id="im", title="I mail")
        im2 = api.content.create(container=self.folder, type="dmsincomingmail", id="im2", title="I mail 2")
        self.assertEqual(self.reply_to_tuples(im), [])
        om = api.content.create(container=self.folder, type="dmsoutgoingmail", id="om", title="O mail")
        om.reply_to = [rel(im)]
        modified(om)
        # the view shows the back references: the reply
        self.assertEqual(self.reply_to_tuples(im), [(om.absolute_url(), "test-out/10 - O mail")])
        im.reply_to = [rel(im2)]
        modified(im)
        self.assertEqual(
            self.reply_to_tuples(im),
            [(im2.absolute_url(), "test-in/11 - I mail 2"), (om.absolute_url(), "test-out/10 - O mail")],
        )
        self.assertEqual(self.reply_to_tuples(im2), [(im.absolute_url(), "test-in/10 - I mail")])


class TestIDmsOutgoingMail(MailSchemaTestCase):
    def test_schema(self):
        schema = dmsmail.IDmsOutgoingMail
        self.assertTrue(schema.isOrExtends(IDmsDocument))
        self.assertIsInstance(schema["sender"], ContactChoice)
        self.assertFalse(schema["sender"].required)
        self.assertIsInstance(schema["recipients"], ContactList)
        self.assertTrue(schema["recipients"].required)
        self.assertEqual(schema["mail_date"].min, datetime.date(1990, 1, 1))
        self.assertEqual(schema["mail_date"].max, datetime.date(TODAY.year + 1, 12, 31))
        for name in ("mail_date", "external_reference_no", "internal_reference_no"):
            self.assertFalse(schema[name].required)
        self.check_reply_to(schema["reply_to"])
        form = self.add_form("dmsoutgoingmail")
        self.assertEqual(list(form.widgets.keys()), OM_FIELDS)
        self.assertIsInstance(form.widgets["sender"], ContactAutocompleteSelectionWidget)
        self.assertIsInstance(form.widgets["recipients"], ContactAutocompleteMultiSelectionWidget)
        # default date widget (no form.widget hint), Plone 6: of plone.app.z3cform (Plone 4: plone.formwidget.datetime)
        self.assertIsInstance(form.widgets["mail_date"], DateWidget)
        self.assertIsInstance(form.widgets["reply_to"], RelatedDocsWidget)

    def test_reply_to(self):
        im = api.content.create(container=self.folder, type="dmsincomingmail", id="im", title="I mail")
        om = api.content.create(container=self.folder, type="dmsoutgoingmail", id="om", title="O mail")
        om2 = api.content.create(container=self.folder, type="dmsoutgoingmail", id="om2", title="O mail 2")
        om.reply_to = [rel(im)]
        modified(om)
        self.assertEqual(self.reply_to_tuples(om), [(im.absolute_url(), "test-in/10 - I mail")])
        # back reference of another outgoing mail
        om2.reply_to = [rel(om)]
        modified(om2)
        self.assertEqual(
            self.reply_to_tuples(om),
            [(im.absolute_url(), "test-in/10 - I mail"), (om2.absolute_url(), "test-out/11 - O mail 2")],
        )


class EmailSchemaTestCase(TestContentTypes):
    """A type using the email schema, as imio.dms.mail does."""

    schema = None

    def setUp(self):
        super(EmailSchemaTestCase, self).setUp()
        fti = DexterityFTI("testemail")
        fti.klass = "plone.dexterity.content.Item"
        fti.schema = self.schema.__identifier__
        self.portal.portal_types._setObject("testemail", fti)
        SCHEMA_CACHE.invalidate("testemail")


class TestIOutgoingEmail(EmailSchemaTestCase):

    schema = dmsmail.IOutgoingEmail

    def test_schema(self):
        schema = dmsmail.IOutgoingEmail
        self.assertEqual(sorted(schema.names()), sorted(EMAIL_FIELDS))
        for name in ("email_subject", "email_sender", "email_recipient", "email_body"):
            self.assertTrue(schema[name].required, name)
        for name in ("email_status", "email_cc", "email_bcc", "email_attachments"):
            self.assertFalse(schema[name].required, name)
        self.assertRaises(RequiredMissing, schema["email_subject"].validate, None)
        # addresses
        schema["email_sender"].validate("Sender <sender@imio.be>")
        self.assertRaises(InvalidEmailAddress, schema["email_sender"].validate, "sender")
        for name in ("email_recipient", "email_cc", "email_bcc"):
            schema[name].validate("a@imio.be, B <b@imio.be>")
            self.assertRaises(InvalidEmailAddress, schema[name].validate, "a@imio.be, b")
        self.assertEqual(
            schema["email_attachments"].value_type.vocabularyName, "collective.dms.mailcontent.email_attachments_voc"
        )
        self.assertIsInstance(schema["email_body"], RichText)
        self.assertEqual(schema["email_body"].allowed_mime_types, ("text/html",))
        # the add form: fields in the default fieldset, attachments as checkboxes
        form = self.add_form("testemail")
        self.assertEqual(list(form.widgets.keys()), EMAIL_FIELDS)
        self.assertIsInstance(form.widgets["email_attachments"], CheckBoxWidget)
        self.assertIsInstance(form.widgets["email_body"], RichTextWidget)
        # the status is only editable by a manager (permissions are checked when the publisher found a user)
        self.request["AUTHENTICATED_USER"] = api.user.get_current()
        self.assertEqual(list(self.add_form("testemail").widgets.keys()), EMAIL_FIELDS)
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        self.assertEqual(list(self.add_form("testemail").widgets.keys()), EMAIL_FIELDS[1:])
        # wrong addresses in the form
        data = {
            "form.widgets.email_subject": "Subject",
            "form.widgets.email_sender": "sender",
            "form.widgets.email_recipient": "a@imio.be,b",
            "form.buttons.save": "Save",
        }
        self.assertEqual(
            sorted(form_errors(self.add_form("testemail", data, "POST"))),
            ["email_body", "email_recipient", "email_sender"],
        )


class TestIFieldsetOutgoingEmail(EmailSchemaTestCase):

    schema = dmsmail.IFieldsetOutgoingEmail

    def test_schema(self):
        self.assertTrue(dmsmail.IFieldsetOutgoingEmail.isOrExtends(dmsmail.IOutgoingEmail))
        form = self.add_form("testemail")
        self.assertEqual(list(form.widgets.keys()), [])
        self.assertEqual([g.__name__ for g in form.groups], ["email"])
        self.assertEqual(form.groups[0].label, "Email")
        self.assertEqual(list(form.groups[0].widgets.keys()), EMAIL_FIELDS)
        self.assertIsInstance(form.groups[0].widgets["email_attachments"], CheckBoxWidget)
