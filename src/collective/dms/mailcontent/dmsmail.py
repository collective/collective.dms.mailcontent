from zope import schema
#from zope.component import adapts
from zope.interface import implements, implementer
from zope.component import adapter
from z3c.form.interfaces import IFormLayer, IFieldWidget
from z3c.form.widget import FieldWidget

from z3c.relationfield.schema import RelationChoice, RelationList
from z3c.relationfield.interfaces import IRelationList

#from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy

#from plone.supermodel import model

from plone.formwidget.contenttree import (
#    ContentTreeFieldWidget,
    ObjPathSourceBinder,
    )
from plone.formwidget.autocomplete.widget import AutocompleteMultiSelectionWidget

from collective.dms.basecontent.dmsdocument import IDmsDocument, DmsDocument

from . import _

class IRelatedDocs(IRelationList):
    """"""

@adapter(IRelatedDocs, IFormLayer)
@implementer(IFieldWidget)
def RelatedDocsFieldWidget(field, request):
    return FieldWidget(field, AutocompleteMultiSelectionWidget(request))


class RelatedDocs(RelationList):
    implements(IRelatedDocs)

    def __init__(self, portal_types, **kwargs):
        RelationList.__init__(self,
                        value_type=RelationChoice(
                            title=u'',
                            source=ObjPathSourceBinder(
                                portal_type=portal_types)),
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
        portal_types=('dmsincomingmail',))


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
