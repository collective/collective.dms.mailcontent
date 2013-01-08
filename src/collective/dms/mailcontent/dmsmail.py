from zope import schema
#from zope.component import adapts
from zope.interface import implements

from z3c.relationfield.schema import RelationChoice, RelationList


#from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy

#from plone.supermodel import model

from plone.formwidget.contenttree import (
#    ContentTreeFieldWidget,
    ObjPathSourceBinder,
    )

from collective.dms.basecontent.dmsdocument import IDmsDocument, DmsDocument

from . import _


class RelatedDocs(RelationList):
    def __init__(self, portal_types, **kwargs):
        RelationList.__init__(self,
                        value_type=RelationChoice(title=u'', source=ObjPathSourceBinder()),
                        **kwargs)


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

    in_reply_to = RelatedDocs(
        title=_(u"In Reply To"),
        required=False,
        portal_types=('dmsoutgoingmail',))


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

    in_reply_to = RelatedDocs(
        title=_(u"In Reply To"),
        required=False,
        portal_types=('dmsoutgoingmail',))


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
