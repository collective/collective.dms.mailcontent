from five import grok

from plone.indexer import indexer

from collective.dms.mailcontent.dmsmail import IDmsIncomingMail


@indexer(IDmsIncomingMail)
def in_reply_to(obj):
    """Avoid conflict with plone.app.discussion in_reply_to indexer"""
    return None

grok.global_adapter(in_reply_to, name='in_reply_to')
