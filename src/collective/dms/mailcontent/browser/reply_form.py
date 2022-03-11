# -*- coding: utf-8 -*-
"""Reply form."""
from collective.dms.mailcontent import _
from collective.dms.mailcontent.browser.views import DmsOutgoingMailUpdateWidgets
from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.utils import addContentToContainer
from Products.CMFPlone.utils import safe_unicode
from zc.relation.interfaces import ICatalog
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from zope.intid.interfaces import IIntIds


class ReplyForm(DefaultAddForm):

    """Form to reply to an incoming mail."""

    description = u""
    portal_type = "dmsoutgoingmail"
    reply_backrefs = True

    def __init__(self, context, request, ti=None):
        super(ReplyForm, self).__init__(context, request, ti=ti)
        self.linked_paths = None

    def _get_linked_mails(self, imail):
        if self.linked_paths is not None:
            return self.linked_paths
        ret = ['/'.join(imail.getPhysicalPath())]
        # get directly imail linked mails
        if imail.reply_to:
            ret.extend([rv.to_path for rv in imail.reply_to])
        # we get backrefs too (depending of an option ?)
        if self.reply_backrefs:
            intids = getUtility(IIntIds)
            catalog = getUtility(ICatalog)
            imail_id = intids.getId(imail)
            for ref in catalog.findRelations({'to_id': imail_id, 'from_attribute': 'reply_to'}):
                if ref.from_path not in ret:
                    ret.append(ref.from_path)
        self.linked_paths = tuple(ret)
        return self.linked_paths

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
        if self.request.get('masterID'):  # in MS anonymous call
            return
        form = self.request.form
        # Completing form values wasn't working anymore, but relations must be set here too !
        # We need to put a value only if key doesn't exist, otherwise the user modifications in form aren't kept
        # Because updateFields is also called after submission
        if "form.widgets.reply_to" not in form:
            form["form.widgets.reply_to"] = self._get_linked_mails(imail)
        if "form.widgets.recipients" not in form:
            form["form.widgets.recipients"] = tuple([sd.to_path for sd in imail.sender])

    def updateWidgets(self, prefix=None):
        super(ReplyForm, self).updateWidgets(prefix=prefix)
        imail = self.context
        self.widgets["IDublinCore.title"].value = safe_unicode(imail.title)
        self.widgets["treating_groups"].value = imail.treating_groups
        if self.request.get('masterID'):  # in MS anonymous call
            return
        self.widgets["reply_to"].value = self._get_linked_mails(imail)
        self.widgets["recipients"].value = tuple([sd.to_path for sd in imail.sender])
        if imail.external_reference_no:
            self.widgets["external_reference_no"].value = imail.external_reference_no
        if imail.recipient_groups:
            self.widgets["recipient_groups"].value = imail.recipient_groups
        DmsOutgoingMailUpdateWidgets(self)

    def add_content(self, obj):
        """Is overrided in inherited view"""
        try:
            utils_view = getMultiAdapter((self.context, self.request), name=u'cdmc-utils')
        except ComponentLookupError:
            return 'Error getting cdmc-utils view...'
        container = utils_view.outgoingmail_folder()
        return container, addContentToContainer(container, obj)

    def add(self, obj):
        """Create outgoing mail in outgoing-mail folder."""
        setattr(obj, '_is_response', True)

        if not self.request.get('_auto_ref', True):
            setattr(obj, '_auto_ref', False)
        # python:request.get('_auto_ref', True) and 'S%04d' % int(number) or 'S/%s/1' % request.get('_irn', '')

        container, new_object = self.add_content(obj)

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

        fti = getUtility(IDexterityFTI, name=self.portal_type)
        if fti.immediate_view:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id, fti.immediate_view]
            )
        else:
            self.immediate_view = "/".join(
                [container.absolute_url(), new_object.id]
            )
