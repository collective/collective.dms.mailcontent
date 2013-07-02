# -*- coding: utf-8 -*-
#
# File: setuphandlers.py
#
# GNU General Public License (GPL)
#

import logging
logger = logging.getLogger('collective.dms.mailcontent: setuphandlers')
from zope.component import queryUtility, getUtility
from plone.registry.interfaces import IRegistry
from zope.i18n.interfaces import ITranslationDomain

def isNotGoodProfile(context):
    return context.readDataFile("collective_dms_mailcontent_marker.txt") is None


def postInstall(context):
    """Called as at the end of the setup process. """
    # the right place for your custom code

    if isNotGoodProfile(context): return
    registry = getUtility(IRegistry)
    if not registry.get('collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number'):
        registry['collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_number'] = 1
    if not registry.get('collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_talexpression'):
        registry['collective.dms.mailcontent.browser.settings.IDmsMailConfig.incomingmail_talexpression'] = u"python:'in/'+number"
    if not registry.get('collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number'):
        registry['collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_number'] = 1
    if not registry.get('collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_talexpression'):
        registry['collective.dms.mailcontent.browser.settings.IDmsMailConfig.outgoingmail_talexpression'] = u"python:'out/'+number"
