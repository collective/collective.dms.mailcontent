from z3c.form.browser.radio import RadioFieldWidget
from zope.interface import alsoProvides
from zope.schema import Choice

from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform import directives as form
from plone.directives.form import default_value
from plone.supermodel import model

from collective.dms.mailcontent import _


class ISendingType(model.Schema):
    """Sending type behavior"""
    sending_type = Choice(title=_(u"Sending type"),
                          vocabulary='SendingTypes',
                          required=False)
    form.widget(sending_type=RadioFieldWidget)


@default_value(field=ISendingType['sending_type'])
def sending_type_default_value(data):
    return "normal"


alsoProvides(ISendingType, IFormFieldProvider)
