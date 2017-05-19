from DateTime import DateTime
from five import grok
from Products.CMFCore.interfaces import ISiteRoot
from zope.interface import Interface
from zope import schema
from plone.z3cform import layout
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from Products.PageTemplates.Expressions import getEngine
from Products.CMFCore.Expression import Expression
from .. import _


class IDmsMailConfig(Interface):
    """
    Configuration of dms mail
    """

    incomingmail_number = schema.Int(
        title=_(u'Number of next incoming mail'),
        description=_(u"This value is used as 'number' variable in linked tal expression"))

    incomingmail_talexpression = schema.TextLine(
        title=_(u"Incoming mail internal reference default value expression"),
        description=_(u"Tal expression where you can use portal, number as variable")
    )

    outgoingmail_number = schema.Int(
        title=_(u'Number of next outgoing mail'),
        description=_(u"This value is used as 'number' variable in linked tal expression"))

    outgoingmail_talexpression = schema.TextLine(
        title=_(u"Outgoing mail internal reference default value expression"),
        description=_(u"Tal expression where you can use portal, number as variable")
    )

    outgoingmail_today_mail_date = schema.Bool(
        title=_(u'Mail date is today'),
        description=_(u"Check if the outgoing mail 'mail date' field will default to today at creation."),
        default=True
    )


class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    schema = IDmsMailConfig
    label = _(u"Dms Mail settings")


class SettingsView(grok.View):
    """
    View which wrap the settings form using ControlPanelFormWrapper to a HTML boilerplate frame.
    """
    grok.name("dmsmailcontent-settings")
    grok.context(ISiteRoot)
    grok.require('plone.app.controlpanel.Site')

    def render(self):
        view_factor = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
        view = view_factor(self.context, self.request)
        return view()

    def evaluateTalExpression(self, expression, portal, number, **kwargs):
        """
            evaluate the expression, considering portal and number in context
        """
        #evaluate the numerotationTALExpression and pass it obj, lastValue and self
        data = {
            'tool': self,
            'number': str(number),
            'portal': portal,
            'date': DateTime(),
        }
        data.update(kwargs)
        res = ''
        try:
            ctx = getEngine().getContext(data)
            res = Expression(expression)(ctx)
        except Exception, msg:
            return 'Error in expression: %s' % msg
        return res
