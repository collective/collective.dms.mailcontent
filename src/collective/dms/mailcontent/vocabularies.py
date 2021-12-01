# -*- coding: utf-8 -*-
"""Vocabularies."""
from collective.dms.basecontent.dmsfile import IDmsAppendixFile
from collective.dms.basecontent.dmsfile import IDmsFile
from collective.dms.mailcontent import _tr
from imio.helpers.content import find
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
        # first we find context files, unrestrictedly
        brains = find(context=context, unrestricted=True, object_provides=[IDmsAppendixFile.__identifier__,
                                                                           IDmsFile.__identifier__])
        for brain in brains:
            terms.append(SimpleTerm(brain.UID, brain.UID, _tr(u'({}) => ${{title}}'.format(brain.portal_type),
                                                              mapping={'title': safe_unicode(brain.Title)})))
        # then we find files of related mails
        pc = api.portal.get_tool('portal_catalog')
        for rv in context.reply_to:
            brains = pc.unrestrictedSearchResults(path=rv.to_path, object_provides=[IDmsAppendixFile.__identifier__,
                                                                                    IDmsFile.__identifier__])
            for brain in brains:
                terms.append(SimpleTerm(brain.UID, brain.UID,
                                        _tr(u'${{ref}} ({}) => ${{title}}'.format(brain.portal_type),
                                            mapping={'ref': rv.to_object.internal_reference_no,
                                                     'title': safe_unicode(brain.Title)})))

        terms.sort(key=lambda trm: trm.title.lower())
        return SimpleVocabulary(terms)
