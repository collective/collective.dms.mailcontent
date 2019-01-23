# -*- coding: utf-8 -*-

from collective.dms.basecontent.browser.views import DmsDocumentEdit
from plone import api
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView


def DmsOutgoingMailUpdateWidgets(the_form):
    """
        Widgets update method for add, edit and reply !
    """
    # context can be the folder in add or an im in reply.
    # store current_user used in sub product imio.dms.mail
    the_form.current_user = api.user.get_current()
    if (not the_form.current_user.has_role(['Manager', 'Site Administrator']) and
            the_form.request.get('_hide_irn', False)):
        the_form.widgets['internal_reference_no'].mode = 'hidden'
        # we empty value to bypass validator when creating object. Reference will be managed automatically
        if the_form.context.portal_type != 'dmsoutgoingmail':
            the_form.widgets['internal_reference_no'].value = ''


class OMEdit(DmsDocumentEdit):
    """
        Edit form redefinition to customize fields.
    """

    def is_initial_state(self):
        pw = api.portal.get_tool('portal_workflow')
        wfs = pw.getWorkflowsFor(self.context)
        if not wfs:
            return True  # when no workflow, consider it's the initial state
        if api.content.get_state(self.context) == wfs[0].initial_state:
            return True
        return False

    def updateFields(self):
        super(OMEdit, self).updateFields()
        edit_irn = api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                  'outgoingmail_edit_irn')
        if edit_irn == 'hide' or (edit_irn == 'reply' and (not getattr(self.context, '_is_response', False) or
                                  not self.is_initial_state())):
            self.request['_hide_irn'] = True
        elif not api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                'outgoingmail_increment_number'):
            self.request['_auto_ref'] = False  # add it to request than can be used in default method, etc...

    def updateWidgets(self):
        super(OMEdit, self).updateWidgets()
        DmsOutgoingMailUpdateWidgets(self)


class OMCustomAddForm(DefaultAddForm):

    portal_type = 'dmsoutgoingmail'

    def updateFields(self):
        super(OMCustomAddForm, self).updateFields()
        edit_irn = api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                  'outgoingmail_edit_irn')
        if edit_irn in ('hide', 'reply'):
            self.request['_hide_irn'] = True
        elif not api.portal.get_registry_record('collective.dms.mailcontent.browser.settings.IDmsMailConfig.'
                                                'outgoingmail_increment_number'):
            self.request['_auto_ref'] = False

    def updateWidgets(self):
        super(OMCustomAddForm, self).updateWidgets()
        DmsOutgoingMailUpdateWidgets(self)
        # the following doesn't work
        # self.widgets['ITask.assigned_user'].value = [api.user.get_current().getId()]

    def add(self, object):
        if not self.request.get('_auto_ref', True):
            setattr(object, '_auto_ref', False)
        super(OMCustomAddForm, self).add(object)


class AddOM(DefaultAddView):

    form = OMCustomAddForm
