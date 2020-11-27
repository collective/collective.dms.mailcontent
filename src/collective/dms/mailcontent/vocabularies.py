# -*- coding: utf-8 -*-
"""Vocabularies."""
from collective.dms.basecontent.dmsfile import IDmsAppendixFile
from collective.dms.basecontent.dmsfile import IDmsFile
from collective.dms.mailcontent import _ as _no  # noqa
from plone import api
from Products.CMFPlone.utils import safe_unicode
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class EmailAttachmentsVocabulary(object):
    """ Vocabulary listing outgoing mail files, as possible email attachments """
    implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        brains = api.content.find(context=context, object_provides=[IDmsAppendixFile.__identifier__,
                                                                    IDmsFile.__identifier__])
        for brain in brains:
            terms.append(SimpleTerm(brain.UID, brain.UID, _no(u'{}: ${{title}}'.format(brain.portal_type),
                                                              mapping={'title': safe_unicode(brain.Title)})))
        terms.sort(key=lambda trm: trm.title.lower())
        return SimpleVocabulary(terms)
