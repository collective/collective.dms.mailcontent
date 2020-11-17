# encoding: utf-8

from collective.dms.mailcontent.dmsmail import IDmsIncomingMail
from Products.Five import BrowserView


class UtilsMethods(BrowserView):
    """ View containing utils methods """

    def outgoingmail_folder(self):
        """ Get a folder for outgoing mail """
        if IDmsIncomingMail.providedBy(self.context):
            return self.context.__parent__
        return self.context
