import datetime

from z3c.form import validator
from zope import schema
from zope.component import getUtility, getMultiAdapter
from zope.component.interfaces import ComponentLookupError
from zope.interface import Invalid
from zope.interface import implements

from Products.CMFPlone.utils import getToolByName

from plone import api
from plone.autoform import directives as form
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.directives.form import default_value
from plone.formwidget.datetime.z3cform.widget import (DateFieldWidget,
                                                      DatetimeFieldWidget)
from plone.indexer import indexer
from plone.registry.interfaces import IRegistry

from Products.PluginIndexes.common.UnIndex import _marker

from collective import dexteritytextindexer
from collective.dms.basecontent.relateddocs import RelatedDocs
from collective.dms.basecontent.dmsdocument import IDmsDocument, DmsDocument
from collective.contact.core.schema import ContactList, ContactChoice

from . import _


def validateIndexValueUniqueness(context, portal_type, index_name, value):
    """
        check at 'portal_type' 'context' creation if 'index' 'value' is uniqueness
    """
    # if the value is empty, we don't check anything
    if not value:
        return
    catalog = getToolByName(context, 'portal_catalog')
    brains = catalog.searchResults(**{index_name: value})
    if context.portal_type != portal_type:
        # we create the dmsincomingmail, the context is the container
        if brains:
            raise Invalid(_(u"This value is already used"))
    else:
        # we edit the type, the context is itself
        # if multiple brains (normally not possible), we are sure there are other objects with same index value
        if len(brains) > 1 or (len(brains) == 1 and brains[0].UID != context.UID()):
            raise Invalid(_(u"This value is already used"))


class InternalReferenceIncomingMailValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        #we call the already defined validators
        #super(InternalReferenceValidator, self).validate(value)
        try:
            validateIndexValueUniqueness(self.context, 'dmsincomingmail',
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
        portal_types=('dmsincomingmail', 'dmsoutgoingmail'),
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


@indexer(IDmsIncomingMail)
def internalReferenceNoIndexerForIncomingMail(obj):
    """
        specific indexer method to avoid acquisition of dmsincomingmail contained elements.
        internal_reference_number is a fake attribute name
    """
    if obj.internal_reference_no:
        return obj.internal_reference_no
    return _marker


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
        portal_types=('dmsincomingmail', 'dmsoutgoingmail'),
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


class InternalReferenceOutgoingMailValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        #we call the already defined validators
        #super(InternalReferenceValidator, self).validate(value)
        try:
            validateIndexValueUniqueness(self.context, 'dmsoutgoingmail',
                                         'internal_reference_number', value)
        except Invalid:
            raise Invalid(_(u"This value is already used. A good value would be: ${good_value}",
                            mapping={'good_value': internalReferenceOutgoingMailDefaultValue(self)}))


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


@indexer(IDmsOutgoingMail)
def internalReferenceNoIndexerForOutgoingMail(obj):
    """
        specific indexer method to avoid acquisition of dmsoutgoingmail contained elements.
        internal_reference_number is a fake attribute name
    """
    if obj.internal_reference_no:
        return obj.internal_reference_no
    return _marker


class DmsIncomingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsIncomingMail, )


class DmsOutgoingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsOutgoingMail, )
