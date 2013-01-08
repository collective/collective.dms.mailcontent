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

    related_items = RelationList(title=u"Related Items (Relations field)",
                           required=False,
                           value_type=RelationChoice(title=u"Multiple",
                                source=ObjPathSourceBinder()))

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
