from plone import api
from zope.component import getUtility
from zope.i18n import ITranslationDomain
from zope.i18nmessageid import MessageFactory

_ = MessageFactory("collective.dms.mailcontent")


def initialize(context):
    """Initializer called when used as a Zope 2 product."""


def _tr(msgid, domain='collective.dms.mailcontent', mapping=None):
    translation_domain = getUtility(ITranslationDomain, domain)
    sp = api.portal.get().portal_properties.site_properties
    return translation_domain.translate(msgid, target_language=sp.getProperty('default_language', 'fr'),
                                        mapping=mapping)
