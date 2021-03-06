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
from zope.intid.interfaces import IIntIds


class ReplyForm(DefaultAddForm):

    """Form to reply to an incoming mail."""

    description = u""
    portal_type = "dmsoutgoingmail"

    @property
    def label(self):
        return _(u"Reply to ${ref}", mapping={'ref': safe_unicode(self.context.Title())})

    def update_fields_irn(self):
        """ update fields regarding irn setting """
        edit_irn = api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                  'outgoingmail_edit_irn')
        self.request['_hide_irn'] = True
        # a user can edit irn. we don't use number incrementation
        if edit_irn in ('show', 'reply'):
            self.request['_hide_irn'] = False
            if not api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                  'outgoingmail_increment_number'):
                self.request['_auto_ref'] = False

    def updateFields(self):
        super(ReplyForm, self).updateFields()
        imail = self.context
        # put original mail irn in request to be used in irn expression
        self.request['_irn'] = imail.internal_reference_no
        self.update_fields_irn()
        form = self.request.form
        # Completing form values wasn't working anymore, but relations must be set here too !
        # We need to put a value only if key doesn't exist, otherwise the user modifications in form aren't kept
        # Because updateFields is also called after submission
        if not "form.widgets.reply_to" in form:
            form["form.widgets.reply_to"] = ('/'.join(imail.getPhysicalPath()),)
        if not "form.widgets.recipients" in form:
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

        # we made sure to add incomingmail treating_groups in recipient_groups if a recipient group has replied
        otgs = obj.treating_groups
        if not isinstance(otgs, (list, tuple)):  # can be a unique value like in imio.dms.mail
            otgs = [otgs]
        intids = getUtility(IIntIds)
        omgs = list(obj.recipient_groups or [])
        for rel in obj.reply_to or []:
            im = intids.getObject(rel.to_id)
            itgs = im.treating_groups
            if not isinstance(itgs, (list, tuple)):  # can be a unique value like in imio.dms.mail
                itgs = [itgs]
            missings = set(itgs) - (set(otgs) | set(omgs))
            for missing in missings:
                obj.recipient_groups.append(missing)
        if omgs != obj.recipient_groups:
            obj.reindexObject(idxs=['recipient_groups'])

        if fti.immediate_view:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id, fti.immediate_view]
            )
        else:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id]
            )
