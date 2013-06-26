from z3c.form.browser.radio import RadioFieldWidget
from zope.interface import alsoProvides
from zope.schema import Choice
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from plone.supermodel import model

from collective.dms.mailcontent import _


sending_types = SimpleVocabulary([
    SimpleTerm(value='normal', title=_(u'Normal')),
    SimpleTerm(value='registered', title=_(u'Registered')),
])


class ISendingType(model.Schema):
    """Sending type behavior"""
    sending_type = Choice(title=_(u"Sending type"),
                          vocabulary=sending_types,
                          default='normal',
                          required=False)
    form.widget(sending_type=RadioFieldWidget)


alsoProvides(ISendingType, IFormFieldProvider)
