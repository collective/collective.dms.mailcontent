from imio.helpers.content import get_relations
from . import _
from collective import dexteritytextindexer
from collective.contact.widget.schema import ContactChoice
from collective.contact.widget.schema import ContactList
from collective.dms.basecontent.dmsdocument import DmsDocument
from collective.dms.basecontent.dmsdocument import IDmsDocument
from collective.dms.basecontent.relateddocs import RelatedDocs
from imio.helpers.emailer import validate_email_address
from imio.helpers.emailer import validate_email_addresses
from plone import api
from plone.app.textfield import RichText
from plone.autoform import directives as form
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.directives.form.value import default_value
from plone.formwidget.datetime.z3cform.widget import DateFieldWidget
from plone.formwidget.datetime.z3cform.widget import DatetimeFieldWidget
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from Products.CMFPlone.utils import getToolByName
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from z3c.form import validator
from zope import schema
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from zope.interface import implements
from zope.interface import Invalid

import datetime


def validateIndexValueUniqueness(context, type_interface, index_name, value):
    """
        check at 'portal_type' 'context' creation if 'index' 'value' is uniqueness
    """
    # if the value is empty, we don't check anything
    if not value:
        return
    catalog = getToolByName(context, 'portal_catalog')
    brains = catalog.searchResults(**{index_name: value})
    if not type_interface.providedBy(context):
        # we create the dmsincomingmail, the context is the container
        if brains:
            raise Invalid(_(u"This value is already used"))
    else:
        # we edit the type, the context is itself
        # if multiple brains (normally not possible), we are sure there are other objects with same index value
        if len(brains) > 1 or (len(brains) == 1 and brains[0].UID != context.UID()):
            raise Invalid(_(u"This value is already used"))


class InternalReferenceBaseValidator(validator.SimpleFieldValidator):

    type_interface = None

    def validate(self, value):
        # we call the already defined validators
        # super(InternalReferenceValidator, self).validate(value)
        try:
            validateIndexValueUniqueness(self.context, self.type_interface,
                                         'internal_reference_number', value)
        except Invalid:
            raise Invalid(_(u"This value is already used. A good value would be: ${good_value}",
                            mapping={'good_value': internalReferenceIncomingMailDefaultValue(self)}))


class IDmsIncomingMail(IDmsDocument):
    """ """

    original_mail_date = schema.Date(
        title=_(u'Original Mail Date'),
        required=False,)
    form.widget(original_mail_date=DateFieldWidget)

    reception_date = schema.Datetime(title=_(u'Reception Date'), required=False)
    form.widget('reception_date', DatetimeFieldWidget, show_time=True)

    external_reference_no = schema.TextLine(
        title=_(u"External Reference Number"),
        required=False,)

    dexteritytextindexer.searchable('internal_reference_no')
    internal_reference_no = schema.TextLine(
        title=_(u"Internal Reference Number"),
        required=False,)

    sender = ContactList(
        title=_(u'Sender'),
        required=True)

    recipients = ContactList(
        title=_(u'Recipients'),
        required=False)

    reply_to = RelatedDocs(
        title=_(u"In Reply To"),
        required=False,
        object_provides=('collective.dms.mailcontent.dmsmail.IDmsIncomingMail',
                         'collective.dms.mailcontent.dmsmail.IDmsOutgoingMail'),
        display_backrefs=True)

    form.order_before(sender='treating_groups')
    form.order_after(recipients='sender')
    form.order_before(original_mail_date='treating_groups')
    form.order_before(reception_date='treating_groups')
    form.order_before(internal_reference_no='treating_groups')
    form.order_before(external_reference_no='treating_groups')
    form.order_before(reply_to='treating_groups')

    form.order_after(related_docs='recipient_groups')
    form.order_after(notes='related_docs')


class InternalReferenceIncomingMailValidator(InternalReferenceBaseValidator):

    type_interface = IDmsIncomingMail


validator.WidgetValidatorDiscriminators(InternalReferenceIncomingMailValidator,
                                        field=IDmsIncomingMail['internal_reference_no'])


@default_value(field=IDmsIncomingMail['reception_date'])
def receptionDateDefaultValue(data):
    # return the current datetime
    return datetime.datetime.now()


@default_value(field=IDmsIncomingMail['original_mail_date'])
def originalMailDateDefaultValue(data):
    # return 3 days before
    return datetime.date.today() - datetime.timedelta(3)


def evaluateInternalReference(context, request, number_registry_name, talexpression_registry_name):
    # return a generated internal reference number
    registry = getUtility(IRegistry)
    # we get the following mail number, stored in registry
    number = registry.get(number_registry_name) or 1
    # we get the portal
    try:
        portal_state = getMultiAdapter((context, request), name=u'plone_portal_state')
        settings_view = getMultiAdapter((portal_state.portal(), request), name=u'dmsmailcontent-settings')
    except ComponentLookupError:
        return 'Error getting view...'
    # we evaluate the expression
    expression = registry.get(talexpression_registry_name)
    value = settings_view.evaluateTalExpression(expression, context, request, portal_state.portal(), number)
    return value


@default_value(field=IDmsIncomingMail['internal_reference_no'])
def internalReferenceIncomingMailDefaultValue(data):
    """
        Default value of internal_reference_no for dmsincomingmail
    """
    return evaluateInternalReference(data.context, data.request,
                                     'collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number',
                                     'collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                     'incomingmail_talexpression').decode('utf8')


class DmsIncomingMail(DmsDocument):
    """ """
    implements(IDmsIncomingMail)
    __ac_local_roles_block__ = False

    def Title(self):
        if self.internal_reference_no is None:
            return self.title.encode('utf8')
        return "%s - %s" % (self.internal_reference_no.encode('utf8'), self.title.encode('utf8'))


def incrementIncomingMailNumber(incomingmail, event):
    """ Increment the value in registry """
    # if internal_reference_no is empty, we force the value.
    # useless if the internal_reference_no field is hidden (in this case,
    #                                                       default value must be empty to bypass validator)
    # useless to manage automatically the internal_reference_no value without user action
    if not incomingmail.internal_reference_no:
        internal_reference_no = evaluateInternalReference(incomingmail, incomingmail.REQUEST,
                                                          'collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                          'incomingmail_number',
                                                          'collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                          'incomingmail_talexpression')
        incomingmail.internal_reference_no = internal_reference_no
        incomingmail.reindexObject(idxs=('Title', 'internal_reference_number', 'SearchableText', 'sortable_title'))
    registry = getUtility(IRegistry)
    registry['collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number'] += 1


class IDmsOutgoingMail(IDmsDocument):
    """ """

    mail_date = schema.Date(title=_(u'Mail Date'), required=False)

    dexteritytextindexer.searchable('internal_reference_no')
    internal_reference_no = schema.TextLine(
        title=_(u"Internal Reference Number"),
        required=False, )

    sender = ContactChoice(
        title=_(u'Sender'),
        required=False)

    recipients = ContactList(
        title=_(u'Recipients'),
        required=True)

    reply_to = RelatedDocs(
        title=_(u"In Reply To"),
        required=False,
        object_provides=('collective.dms.mailcontent.dmsmail.IDmsIncomingMail',
                         'collective.dms.mailcontent.dmsmail.IDmsOutgoingMail'),
        display_backrefs=True)

    external_reference_no = schema.TextLine(
        title=_(u"External Reference Number"),
        required=False,)

    form.order_before(sender='treating_groups')
    form.order_before(recipients='treating_groups')
    form.order_before(mail_date='treating_groups')
    form.order_before(internal_reference_no='treating_groups')
    form.order_before(external_reference_no='treating_groups')
    form.order_before(reply_to='treating_groups')

    form.order_after(related_docs='recipient_groups')
    form.order_after(notes='related_docs')


@default_value(field=IDmsOutgoingMail['mail_date'])
def mailDateDefaultValue(data):
    # return the day date
    today = api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                           'outgoingmail_today_mail_date')
    if today:
        return datetime.date.today()


@default_value(field=IDmsOutgoingMail['internal_reference_no'])
def internalReferenceOutgoingMailDefaultValue(data):
    """
        Default value of internal_reference_no for dmsoutgoingmail
    """
    return evaluateInternalReference(data.context, data.request,
                                     'collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number',
                                     'collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                     'outgoingmail_talexpression').decode('utf8')


class InternalReferenceOutgoingMailValidator(InternalReferenceBaseValidator):
    type_interface = IDmsOutgoingMail


validator.WidgetValidatorDiscriminators(InternalReferenceOutgoingMailValidator,
                                        field=IDmsOutgoingMail['internal_reference_no'])


def incrementOutgoingMailNumber(outgoingmail, event):
    """ Increment the value in registry """
    # if internal_reference_no is empty, we force the value.
    # useful if the internal_reference_no field is hidden (in this case,
    #                                                      default value must be empty to bypass validator)
    # useful to manage automatically the internal_reference_no value without user action
    if not outgoingmail.internal_reference_no:
        internal_reference_no = evaluateInternalReference(outgoingmail, outgoingmail.REQUEST,
                                                          'collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                          'outgoingmail_number',
                                                          'collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                          'outgoingmail_talexpression')
        outgoingmail.internal_reference_no = internal_reference_no
        outgoingmail.reindexObject(idxs=('Title', 'internal_reference_number', 'SearchableText', 'sortable_title'))
    if getattr(outgoingmail, '_auto_ref', True):
        registry = getUtility(IRegistry)
        registry['collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number'] += 1


class DmsOutgoingMail(DmsDocument):
    """ """
    implements(IDmsOutgoingMail)

    def Title(self):
        if self.internal_reference_no is None:
            return self.title.encode('utf8')
        return "%s - %s" % (self.internal_reference_no.encode('utf8'), self.title.encode('utf8'))

    def get_replied(self, first=True, intf=IDmsIncomingMail):
        normals = [obj for obj in get_relations(self, 'reply_to', backrefs=False, as_obj=True)
                   if intf.providedBy(obj)]
        backs = [obj for obj in get_relations(self, 'reply_to', backrefs=True, as_obj=True)
                 if intf.providedBy(obj)]
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
        title=_(u"Email status"),
        required=False,
    )
    form.write_permission(email_status='cmf.ManagePortal')

    email_subject = schema.TextLine(
        title=_(u"Email subject"),
    )

    email_sender = schema.TextLine(
        title=_(u"Email sender"),
        constraint=validate_email_address,
    )

    email_recipient = schema.TextLine(
        title=_(u"Email recipient"),
        description=_(u"Multiple values must be separated by a comma."),
        constraint=validate_email_addresses,
    )

    email_cc = schema.TextLine(
        title=_(u"Email cc"),
        # description=_(u"Multiple values must be separated by a comma."),
        required=False,
        constraint=validate_email_addresses,
    )

    email_attachments = schema.List(
        title=_(u"Email attachments"),
        required=False,
        value_type=schema.Choice(vocabulary=u'collective.dms.mailcontent.email_attachments_voc'),
    )
    form.widget('email_attachments', CheckBoxFieldWidget, multiple='multiple', size=10)

    email_body = RichText(
        title=_(u"Email body"),
        allowed_mime_types=(u"text/html",),
    )


class IFieldsetOutgoingEmail(IOutgoingEmail):
    """ """

    fieldset(
        'email',
        label=_(u"Email"),
        fields=['email_status', 'email_subject', 'email_sender', 'email_recipient', 'email_cc', 'email_attachments',
                'email_body']
    )


class DmsIncomingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsIncomingMail, )


class DmsOutgoingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsOutgoingMail, )
