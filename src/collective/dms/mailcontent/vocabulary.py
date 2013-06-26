from five import grok

from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory

from . import _


class SendingTypes(grok.GlobalUtility):
    grok.name("SendingTypes")
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        types = [('normal', _("Normal")),
                 ('registered', _("Registered"))]
        for (token, value) in types:
            term = SimpleVocabulary.createTerm(token, token, value)
            terms.append(term)
        return SimpleVocabulary(terms)
