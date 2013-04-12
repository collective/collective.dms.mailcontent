from zope.i18nmessageid import MessageFactory

_ = MessageFactory("collective.dms.mailcontent")


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
