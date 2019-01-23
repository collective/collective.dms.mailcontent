# encoding: utf-8

from Products.Five import BrowserView


class UtilsMethods(BrowserView):
    """ View containing utils methods """

    def outgoingmail_folder(self):
        """ Get a folder for outgoing mail """
        if self.context.portal_type == 'dmsincomingmail':
            return self.context.__parent__
        return self.context
