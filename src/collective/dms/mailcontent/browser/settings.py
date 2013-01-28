from DateTime import DateTime
from five import grok
from Products.CMFCore.interfaces import ISiteRoot

from plone.z3cform import layout
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from collective.dms.mailcontent.dmsmail import IDmsIncomingMailInternalReferenceDefaultConfig
from Products.PageTemplates.Expressions import getEngine
from Products.CMFCore.Expression import Expression
from .. import _

class SettingsEditForm(RegistryEditForm):
    """
    Define form logic
    """
    schema = IDmsIncomingMailInternalReferenceDefaultConfig
    label = _(u"Dms Mail settings")

class SettingsView(grok.CodeView):
    """
    View which wrap the settings form using ControlPanelFormWrapper to a HTML boilerplate frame.
    """
    grok.name("dmsmailcontent-settings")
    grok.context(ISiteRoot)
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
            return 'Error in expression: %s'%msg
        return res
