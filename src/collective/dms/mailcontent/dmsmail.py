import datetime
from zope import schema
#from zope.component import adapts
from zope.interface import implements, Interface
from zope.interface import Invalid
from zope.component import getUtility, getMultiAdapter
from zope.component.interfaces import ComponentLookupError
from zope.app.container.interfaces import IObjectAddedEvent
from plone.registry.interfaces import IRegistry
from five import grok
from Products.CMFPlone.utils import getToolByName
#from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from z3c.form import validator
from collective.dms.basecontent.relateddocs import RelatedDocs

#from plone.supermodel import model

from collective.dms.basecontent.dmsdocument import IDmsDocument, DmsDocument
from collective.contact.core.schema import ContactList, ContactChoice

from . import _

from plone.autoform import directives as form
from plone.directives.form import default_value

def validateIndexValueUniqueness(context, portal_type, index_name, value):
    """
        check at 'portal_type' 'context' creation if 'index' 'value' is uniqueness
    """
    catalog = getToolByName(context, 'portal_catalog')
    brains = catalog.searchResults(**{index_name:value})
    if context.portal_type != portal_type:
        # we create the dmsincomingmail, the context is the container
        if brains:
            raise Invalid(_(u"This value is already used"))
    else:
        # we edit the type, the context is itself
        # if multiple brains (normally not possible), we are sure there are other objects with same index value
        if len(brains) >1 or (len(brains)== 1 and brains[0].UID != context.UID()):
            raise Invalid(_(u"This value is already used"))

class InternalReferenceIncomingMailValidator(validator.SimpleFieldValidator):
    def validate(self, value):
        #we call the already defined validators
        #super(InternalReferenceValidator, self).validate(value)
        #import ipdb; ipdb.set_trace()
        validateIndexValueUniqueness(self.context, 'dmsincomingmail', 'internal_reference_no', value)



class IDmsIncomingMail(IDmsDocument):
    """ """

    original_mail_date = schema.Date(title=_(u'Original Mail Date'), required=False)

    reception_date = schema.Date(title=_(u'Reception Date'), required=False)

    external_reference_no = schema.TextLine(
        title=_(u"External Reference Number"),
        required=False
        )

    internal_reference_no = schema.TextLine(
        title=_(u"Internal Reference Number"),
        required=False,
        )

    sender = ContactChoice(
        title=_(u'Sender'),
        required=True)

    in_reply_to = RelatedDocs(
        title=_(u"In Reply To"),
        required=False,
        portal_types=('dmsoutgoingmail',))

    form.order_before(sender='treating_groups')
    form.order_before(original_mail_date='treating_groups')
    form.order_before(reception_date='treating_groups')
    form.order_before(internal_reference_no='treating_groups')
    form.order_before(external_reference_no='treating_groups')
    form.order_before(in_reply_to='treating_groups')

    form.order_after(related_docs='recipient_groups')
    form.order_after(notes='related_docs')

validator.WidgetValidatorDiscriminators(InternalReferenceIncomingMailValidator, field=IDmsIncomingMail['internal_reference_no'])
grok.global_adapter(InternalReferenceIncomingMailValidator)

@default_value(field=IDmsIncomingMail['reception_date'])
def receptionDateDefaultValue(data):
    # return the day date
    return datetime.date.today()

#@default_value(field=IDmsIncomingMail['original_mail_date'])
def originalMailDateDefaultValue(data):
    # return 3 days before
    return datetime.date.today()-datetime.timedelta(3)

@default_value(field=IDmsIncomingMail['internal_reference_no'])
def internalReferenceDefaultValue(data):
    # return a generated internal reference number
    registry = getUtility(IRegistry)
    # we get the following mail number, stored in registry
    number = registry.get('collective.dms.mailcontent.dmsmail.IDmsIncomingMailInternalReferenceDefaultConfig.incoming_mail_number') or 1
    # we get the portal
    try:
        portal_state = getMultiAdapter((data.context, data.request), name=u'plone_portal_state')
        settings_view = getMultiAdapter((portal_state.portal(), data.request), name=u'dmsmailcontent-settings')
    except ComponentLookupError:
        return 'Error getting view...'
    # we evaluate the expression
    expression = registry.get('collective.dms.mailcontent.dmsmail.IDmsIncomingMailInternalReferenceDefaultConfig.tal_expression')
    value = settings_view.evaluateTalExpression(expression, portal_state.portal(), number)
    return value

class DmsIncomingMail(DmsDocument):
    """ """
    implements(IDmsIncomingMail)

class IDmsIncomingMailInternalReferenceDefaultConfig(Interface):
    """
    Configuration of internal reference default value expression for incoming mail
    """

    incoming_mail_number = schema.Int(
        title=_(u'Number of next incoming mail'),
        description=_(u"This value is used as 'number' variable in linked tal expression"))

    tal_expression = schema.TextLine(
        title=_(u"Incoming mail internal reference default value expression"),
        description=_(u"Tal expression where you can use portal, number as variable")
        )

@grok.subscribe(IDmsIncomingMail, IObjectAddedEvent)
def incrementIncomingMailNumber(incomingmail, event):
    """ Increment the value in registry """
    registry = getUtility(IRegistry)
    registry['collective.dms.mailcontent.dmsmail.IDmsIncomingMailInternalReferenceDefaultConfig.incoming_mail_number'] += 1

class IDmsOutgoingMail(IDmsDocument):
    """ """

    mail_date = schema.Date(title=_(u'Mail Date'), required=False)

    internal_reference_no = schema.TextLine(
        title=_(u"Internal Reference Number"),
        required=False
        )

    recipients = ContactList(
        title=_(u'Recipients'),
        required=True)

    in_reply_to = RelatedDocs(
        title=_(u"In Reply To"),
        required=False,
        portal_types=('dmsincomingmail',))

    form.order_before(recipients='treating_groups')
    form.order_before(mail_date='treating_groups')
    form.order_before(internal_reference_no='treating_groups')
    form.order_before(in_reply_to='treating_groups')

    form.order_after(related_docs='recipient_groups')
    form.order_after(notes='related_docs')


class DmsOutgoingMail(DmsDocument):
    """ """
    implements(IDmsOutgoingMail)


class DmsIncomingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsIncomingMail, )


class DmsOutgoingMailSchemaPolicy(DexteritySchemaPolicy):
    """ """

    def bases(self, schemaName, tree):
        return (IDmsOutgoingMail, )
