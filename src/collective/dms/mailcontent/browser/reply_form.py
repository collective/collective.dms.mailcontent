# -*- coding: utf-8 -*-
"""Reply form."""
from collective.dms.mailcontent import _
from collective.dms.mailcontent.browser.views import DmsOutgoingMailUpdateWidgets
from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from Products.CMFPlone.utils import safe_unicode
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError


class ReplyForm(DefaultAddForm):

    """Form to reply to an incoming mail."""

    description = u""
    portal_type = "dmsoutgoingmail"

    @property
    def label(self):
        return _(u"Reply to ${ref}", mapping={'ref': safe_unicode(self.context.Title())})

    def updateFields(self):

        super(ReplyForm, self).updateFields()
        imail = self.context
        # put original mail irn in request to be used in irn expression
        self.request['_irn'] = imail.internal_reference_no

        edit_irn = api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                  'outgoingmail_edit_irn')
        self.request['_hide_irn'] = True
        # a user can edit irn. we don't use number incrementation
        if edit_irn in ('show', 'reply'):
            self.request['_hide_irn'] = False
            if not api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                  'outgoingmail_increment_number'):
                self.request['_auto_ref'] = False

        form = self.request.form
        # Completing form values wasn't working anymore, but relations must be set here too !
        form["form.widgets.reply_to"] = ('/'.join(imail.getPhysicalPath()),)
        form["form.widgets.recipients"] = tuple([sd.to_path for sd in imail.sender])

    def updateWidgets(self):
        super(ReplyForm, self).updateWidgets()
        imail = self.context
        self.widgets["IDublinCore.title"].value = safe_unicode(imail.title)
        self.widgets["treating_groups"].value = imail.treating_groups
        self.widgets["reply_to"].value = ('/'.join(imail.getPhysicalPath()),)
        self.widgets["recipients"].value = tuple([sd.to_path for sd in imail.sender])
        if imail.external_reference_no:
            self.widgets["external_reference_no"].value = imail.external_reference_no
        if imail.recipient_groups:
            self.widgets["recipient_groups"].value = imail.recipient_groups
        DmsOutgoingMailUpdateWidgets(self)

    def add(self, obj):
        """Create outgoing mail in outgoing-mail folder."""
        fti = getUtility(IDexterityFTI, name=self.portal_type)
        try:
            utils_view = getMultiAdapter((self.context, self.request), name=u'cdmc-utils')
        except ComponentLookupError:
            return 'Error getting cdmc-utils view...'
        container = utils_view.outgoingmail_folder()
        setattr(obj, '_is_response', True)

        if not self.request.get('_auto_ref', True):
            setattr(obj, '_auto_ref', False)
        # python:request.get('_auto_ref', True) and 'S%04d' % int(number) or 'S/%s/1' % request.get('_irn', '')

        new_object = addContentToContainer(container, obj)

        if fti.immediate_view:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id, fti.immediate_view]
            )
        else:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id]
            )
