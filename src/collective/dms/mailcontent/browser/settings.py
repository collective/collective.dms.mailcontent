from collective.dms.mailcontent import _
from DateTime import DateTime
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.supermodel import model
from plone.z3cform import layout
from Products.CMFCore.Expression import Expression
from Products.PageTemplates.Expressions import getEngine
from zope import schema
from zope.publisher.browser import BrowserPage
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


im_irn_conditions = SimpleVocabulary([SimpleTerm(u"show", title=_("Always show")),
                                      SimpleTerm(u"hide", title=_("Always hide"))])

om_irn_conditions = SimpleVocabulary([SimpleTerm(u"show", title=_("Always show")),
                                      SimpleTerm(u"hide", title=_("Always hide")),
                                      SimpleTerm(u"reply", title=_("Show only when replying"))])


class IDmsMailConfig(model.Schema):
    """
    Configuration of dms mail
    """

    model.fieldset(
        'incomingmail',
        label=_(u"Incoming mail"),
        fields=['incomingmail_number', 'incomingmail_talexpression']
    )

    incomingmail_number = schema.Int(
        title=_(u'Number of next incoming mail'),
        description=_(u"This value is used as 'number' variable in linked tal expression"))

    incomingmail_talexpression = schema.TextLine(
        title=_(u"Incoming mail internal reference default value expression"),
        description=_(u"Tal expression where you can use portal, number, context, request, date as variable")
    )

    model.fieldset(
        'outgoingmail',
        label=_(u"Outgoing mail"),
        fields=['outgoingmail_number', 'outgoingmail_talexpression', 'outgoingmail_edit_irn',
                'outgoingmail_increment_number', 'outgoingmail_today_mail_date']
    )

    outgoingmail_number = schema.Int(
        title=_(u'Number of next outgoing mail'),
        description=_(u"This value is used as 'number' variable in linked tal expression"))

    outgoingmail_talexpression = schema.TextLine(
        title=_(u"Outgoing mail internal reference default value expression"),
        description=_(u"Tal expression where you can use portal, number, context, request, date as variable")
    )

    outgoingmail_edit_irn = schema.Choice(
        title=_(u"Internal reference number edition field"),
        vocabulary=om_irn_conditions,
        default='show'
    )

    outgoingmail_increment_number = schema.Bool(
        title=_(u"Increment number used in internal reference number"),
        description=_(u"If False, number will not be incremented only if user can edit internal reference number"),
        default=True
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


class SettingsView(BrowserPage):
    """
    View which wrap the settings form using ControlPanelFormWrapper to a HTML boilerplate frame.
    """

    def __call__(self):
        view_factor = layout.wrap_form(SettingsEditForm, ControlPanelFormWrapper)
        view = view_factor(self.context, self.request)
        return view()

    def evaluateTalExpression(self, expression, context, request, portal, number, **kwargs):
        """
            evaluate the expression, considering portal and number in context
        """
        #evaluate the numerotationTALExpression and pass it obj, lastValue and self
        data = {
            'tool': self,
            'number': str(number),
            'context': context,
            'request': request,
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
