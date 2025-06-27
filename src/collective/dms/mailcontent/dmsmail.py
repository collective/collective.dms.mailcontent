from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.dms.basecontent.dmsdocument import DmsDocument
from collective.dms.basecontent.dmsdocument import IDmsDocument
from collective.dms.basecontent.relateddocs import RelatedDocs
from collective.dms.mailcontent import _
from imio.helpers.content import get_relations
from imio.helpers.emailer import validate_email_address
from imio.helpers.emailer import validate_email_addresses
from plone import api
from plone.app.dexterity import textindexer
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from Products.CMFPlone.utils import getToolByName
from z3c.form import validator
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface import provider
from zope.interface.interfaces import ComponentLookupError
from zope.schema.interfaces import IContextAwareDefaultFactory

import datetime


# TODO: MIGRATION-PLONE6
# from plone.formwidget.datetime.z3cform.widget import DateFieldWidget
# from plone.formwidget.datetime.z3cform.widget import DatetimeFieldWidget


def validateIndexValueUniqueness(context, type_interface, index_name, value):
    """
    check at 'portal_type' 'context' creation if 'index' 'value' is uniqueness
    """
    # if the value is empty, we don't check anything
    if not value:
        return
    catalog = getToolByName(context, "portal_catalog")
    brains = catalog.searchResults(**{index_name: value})
    if not type_interface.providedBy(context):
        # we create the dmsincomingmail, the context is the container
        if brains:
            raise Invalid(_("This value is already used"))
    else:
        # we edit the type, the context is itself
        # if multiple brains (normally not possible), we are sure there are other objects with same index value
        if len(brains) > 1 or (len(brains) == 1 and brains[0].UID != context.UID()):
            raise Invalid(_("This value is already used"))


class InternalReferenceBaseValidator(validator.SimpleFieldValidator):

    type_interface = None

    def good_value(self):
        return ""

    def validate(self, value, force=False):
        # we call the already defined validators
        # super(InternalReferenceValidator, self).validate(value)
        try:
            validateIndexValueUniqueness(self.context, self.type_interface, "internal_reference_number", value)
        except Invalid:
            raise Invalid(
                _(
                    "This value is already used. A good value would be: ${good_value}",
                    mapping={"good_value": self.good_value()},
                )
            )


class ReplyToValidator(validator.SimpleFieldValidator):
    """Validates reply_to field to check if selected object is not itself."""

    def validate(self, value, force=False):
        # we call the already defined validators
        super(ReplyToValidator, self).validate(value, force=force)
        # value contains a list of linked objects
        # on reply, self.context is an incomingmail and future outgoingmail cannot be selected
        if self.view.__name__ == "reply":
            return
        if self.context in value or []:
            raise Invalid(
                _(
                    "You cannot choose the current object as a reply to.",
                )
            )


def receptionDateDefaultValue():
    # return the current datetime
    return datetime.datetime.now()


def originalMailDateDefaultValue():
    # return 3 days before
    return datetime.date.today() - datetime.timedelta(days=3)


@provider(IContextAwareDefaultFactory)
def internalReferenceIncomingMailDefaultValue(context):
    """
    Default value of internal_reference_no for dmsincomingmail
    """
    return evaluateInternalReference(
        context,
        getRequest(),
        "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number",
        "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_talexpression",
    )


class IDmsIncomingMail(IDmsDocument):
    """ """

    original_mail_date = schema.Date(
        title=_("Original Mail Date"),
        required=False,
        min=datetime.date(1990, 1, 1),
        max=datetime.date.today() + datetime.timedelta(days=7),
        defaultFactory=originalMailDateDefaultValue,
    )
    # TODO: MIGRATION-PLONE6
    # form.widget(original_mail_date=DateFieldWidget)

    reception_date = schema.Datetime(
        title=_("Reception Date"),
        required=False,
        min=datetime.datetime(1990, 1, 1),
        max=datetime.datetime.today() + datetime.timedelta(days=7),
        defaultFactory=receptionDateDefaultValue,
    )
    # TODO: MIGRATION-PLONE6
    # form.widget("reception_date", DatetimeFieldWidget, show_time=True)

    external_reference_no = schema.TextLine(
        title=_("External Reference Number"),
        required=False,
    )

    textindexer.searchable("internal_reference_no")
    internal_reference_no = schema.TextLine(
        title=_("Internal Reference Number"),
        required=False,
        defaultFactory=internalReferenceIncomingMailDefaultValue,
    )

    sender = ContactList(title=_("Sender"), required=True)

    recipients = ContactList(title=_("Recipients"), required=False)

    reply_to = RelatedDocs(
        title=_("In Reply To"),
        required=False,
        object_provides=(
            "collective.dms.mailcontent.dmsmail.IDmsIncomingMail",
            "collective.dms.mailcontent.dmsmail.IDmsOutgoingMail",
        ),
        display_backrefs=True,
    )

    form.order_before(sender="treating_groups")
    form.order_after(recipients="sender")
    form.order_before(original_mail_date="treating_groups")
    form.order_before(reception_date="treating_groups")
    form.order_before(internal_reference_no="treating_groups")
    form.order_before(external_reference_no="treating_groups")
    form.order_before(reply_to="treating_groups")

    form.order_after(related_docs="recipient_groups")
    form.order_after(notes="related_docs")


class InternalReferenceIncomingMailValidator(InternalReferenceBaseValidator):

    type_interface = IDmsIncomingMail

    def good_value(self):
        return internalReferenceIncomingMailDefaultValue(self.context)


class IMReplyToValidator(ReplyToValidator):
    """IM reply_to validator class"""


validator.WidgetValidatorDiscriminators(
    InternalReferenceIncomingMailValidator, field=IDmsIncomingMail["internal_reference_no"]
)
validator.WidgetValidatorDiscriminators(IMReplyToValidator, field=IDmsIncomingMail["reply_to"])


def evaluateInternalReference(context, request, number_registry_name, talexpression_registry_name):
    """Return a generated internal reference number"""
    registry = getUtility(IRegistry)
    # we get the following mail number, stored in registry
    number = registry.get(number_registry_name) or 1
    # we get the portal
    try:
        portal = api.portal.get()
        settings_view = getMultiAdapter((portal, request), name="dmsmailcontent-settings")
    except ComponentLookupError:
        return "Error getting view..."
    # we evaluate the expression
    expression = registry.get(talexpression_registry_name)
    value = settings_view.evaluateTalExpression(expression, context, request, portal, number)
    return value


@implementer(IDmsIncomingMail)
class DmsIncomingMail(DmsDocument):
    """ """

    __ac_local_roles_block__ = False

    def Title(self):
        if self.internal_reference_no is None:
            return self.title
        return "%s - %s" % (self.internal_reference_no, self.title)


def incrementIncomingMailNumber(incomingmail, event):
    """Increment the value in registry"""
    # if internal_reference_no is empty, we force the value.
    # useless if the internal_reference_no field is hidden (in this case,
    #                                                       default value must be empty to bypass validator)
    # useless to manage automatically the internal_reference_no value without user action
    # to be sure checking the value is really set and not getting default value when accessing fieldname
    if "internal_reference_no" not in incomingmail.__dict__:
        internal_reference_no = evaluateInternalReference(
            incomingmail,
            getRequest(),
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number",
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_talexpression",
        )
        incomingmail.internal_reference_no = internal_reference_no
        incomingmail.reindexObject(idxs=("Title", "internal_reference_number", "SearchableText", "sortable_title"))
    registry = getUtility(IRegistry)
    registry["collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number"] += 1


def mailDateDefaultValue():
    # return the day date
    today = api.portal.get_registry_record(
        "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_today_mail_date"
    )
    if today:
        return datetime.date.today()


@provider(IContextAwareDefaultFactory)
def internalReferenceOutgoingMailDefaultValue(context):
    """
    Default value of internal_reference_no for dmsoutgoingmail
    """

    return evaluateInternalReference(
        context,
        getRequest(),
        "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number",
        "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_talexpression",
    )


class IDmsOutgoingMail(IDmsDocument):
    """ """

    mail_date = schema.Date(
        title=_("Mail Date"),
        required=False,
        min=datetime.date(1990, 1, 1),
        max=datetime.date(datetime.date.today().year + 1, 12, 31),
        defaultFactory=mailDateDefaultValue,
    )

    textindexer.searchable("internal_reference_no")
    internal_reference_no = schema.TextLine(
        title=_("Internal Reference Number"),
        required=False,
        defaultFactory=internalReferenceOutgoingMailDefaultValue,
    )

    sender = ContactChoice(title=_("Sender"), required=False)

    recipients = ContactList(title=_("Recipients"), required=True)

    reply_to = RelatedDocs(
        title=_("In Reply To"),
        required=False,
        object_provides=(
            "collective.dms.mailcontent.dmsmail.IDmsIncomingMail",
            "collective.dms.mailcontent.dmsmail.IDmsOutgoingMail",
        ),
        display_backrefs=True,
    )

    external_reference_no = schema.TextLine(
        title=_("External Reference Number"),
        required=False,
    )

    form.order_before(sender="treating_groups")
    form.order_before(recipients="treating_groups")
    form.order_before(mail_date="treating_groups")
    form.order_before(internal_reference_no="treating_groups")
    form.order_before(external_reference_no="treating_groups")
    form.order_before(reply_to="treating_groups")

    form.order_after(related_docs="recipient_groups")
    form.order_after(notes="related_docs")


class InternalReferenceOutgoingMailValidator(InternalReferenceBaseValidator):
    type_interface = IDmsOutgoingMail

    def good_value(self):
        return internalReferenceOutgoingMailDefaultValue(self.context)


class OMReplyToValidator(ReplyToValidator):
    """OM reply_to validator class"""


validator.WidgetValidatorDiscriminators(
    InternalReferenceOutgoingMailValidator, field=IDmsOutgoingMail["internal_reference_no"]
)
validator.WidgetValidatorDiscriminators(OMReplyToValidator, field=IDmsOutgoingMail["reply_to"])


def incrementOutgoingMailNumber(outgoingmail, event):
    """Increment the value in registry"""
    # if internal_reference_no is empty, we force the value.
    # useful if the internal_reference_no field is hidden (in this case,
    #                                                      default value must be empty to bypass validator)
    # useful to manage automatically the internal_reference_no value without user action
    # to be sure checking the value is really set and not getting default value when accessing fieldname
    if "internal_reference_no" not in outgoingmail.__dict__:
        internal_reference_no = evaluateInternalReference(
            outgoingmail,
            getRequest(),
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number",
            "collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_talexpression",
        )
        outgoingmail.internal_reference_no = internal_reference_no
        outgoingmail.reindexObject(idxs=("Title", "internal_reference_number", "SearchableText", "sortable_title"))
    if getattr(outgoingmail, "_auto_ref", True):
        registry = getUtility(IRegistry)
        registry["collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number"] += 1


@implementer(IDmsOutgoingMail)
class DmsOutgoingMail(DmsDocument):
    """ """

    def Title(self):
        if self.internal_reference_no is None:
            return self.title
        return "%s - %s" % (self.internal_reference_no, self.title)

    def get_replied(self, first=True, intf=IDmsIncomingMail):
        normals = [obj for obj in get_relations(self, "reply_to", backrefs=False, as_obj=True) if intf.providedBy(obj)]
        backs = [obj for obj in get_relations(self, "reply_to", backrefs=True, as_obj=True) if intf.providedBy(obj)]
        for obj in backs:
            if obj not in normals:
                normals.append(obj)
        if first:
            return normals and normals[0] or None
        else:
            return normals


class IOutgoingEmail(model.Schema):
    """ """

    email_status = schema.TextLine(
        title=_("Email status"),
        required=False,
    )
    form.write_permission(email_status="cmf.ManagePortal")

    email_subject = schema.TextLine(
        title=_("Email subject"),
    )

    email_sender = schema.TextLine(
        title=_("Email sender"),
        constraint=validate_email_address,
    )

    email_recipient = schema.TextLine(
        title=_("Email recipient"),
        description=_("Multiple values must be separated by a comma."),
        constraint=validate_email_addresses,
    )

    email_cc = schema.TextLine(
        title=_("Email cc"),
        # description=_(u"Multiple values must be separated by a comma."),
        required=False,
        constraint=validate_email_addresses,
    )

    email_bcc = schema.TextLine(
        title=_("Email bcc"),
        # description=_(u"Hidden emails."),
        required=False,
        constraint=validate_email_addresses,
    )

    email_attachments = schema.List(
        title=_("Email attachments"),
        required=False,
        value_type=schema.Choice(vocabulary="collective.dms.mailcontent.email_attachments_voc"),
    )
    form.widget("email_attachments", CheckBoxFieldWidget, multiple="multiple", size=10)

    email_body = RichText(
        title=_("Email body"),
        allowed_mime_types=("text/html",),
    )


class IFieldsetOutgoingEmail(IOutgoingEmail):
    """ """

    fieldset(
        "email",
        label=_("Email"),
        fields=[
            "email_status",
            "email_subject",
            "email_sender",
            "email_recipient",
            "email_cc",
            "email_bcc",
            "email_attachments",
            "email_body",
        ],
    )


class DmsIncomingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsIncomingMail,)


class DmsOutgoingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsOutgoingMail,)
