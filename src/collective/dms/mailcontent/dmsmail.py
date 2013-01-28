import datetime
from zope import schema
#from zope.component import adapts
from zope.interface import implements, Interface
from zope.component import getUtility
from zope.app.container.interfaces import IObjectAddedEvent
from plone.registry.interfaces import IRegistry
from five import grok

#from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy

from collective.dms.basecontent.relateddocs import RelatedDocs

#from plone.supermodel import model

from collective.dms.basecontent.dmsdocument import IDmsDocument, DmsDocument
from collective.contact.content.schema import ContactList, ContactChoice

from . import _

from plone.autoform import directives as form
from plone.directives.form import default_value

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
        required=False
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
    number = registry.get('collective.dms.mailcontent.dmsmail.IDmsIncomingMailInternalReferenceDefaultConfig.incoming_mail_number') or 1
    return number

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
