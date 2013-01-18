import datetime
from zope import schema
#from zope.component import adapts
from zope.interface import implements

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

@default_value(field=IDmsIncomingMail['original_mail_date'])
def originalMailDateDefaultValue(data):
    # return 3 days before
    return datetime.date.today()-datetime.timedelta(3)


class DmsIncomingMail(DmsDocument):
    """ """
    implements(IDmsIncomingMail)


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
