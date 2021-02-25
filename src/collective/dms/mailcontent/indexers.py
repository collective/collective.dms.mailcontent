from collective.dms.basecontent.dmsdocument import IDmsDocument
from collective.dms.mailcontent.dmsmail import IDmsIncomingMail
from collective.dms.mailcontent.dmsmail import IDmsOutgoingMail
from plone.indexer import indexer
from Products.CMFPlone.utils import base_hasattr
from Products.PluginIndexes.common.UnIndex import _marker


@indexer(IDmsIncomingMail)
def im_internal_reference_number_indexer(obj):
    """Indexer of 'internal_reference_number' for IDmsIncomingMail. Stores internal_reference_no.
    Specific indexer method to avoid acquisition of dmsincomingmail contained elements.
    """
    if obj.internal_reference_no:
        return obj.internal_reference_no
    return _marker


@indexer(IDmsOutgoingMail)
def om_internal_reference_number_indexer(obj):
    """Indexer of 'internal_reference_number' for IDmsOutgoingMail. Stores internal_reference_no.
    Specific indexer method to avoid acquisition of dmsoutgoingmail contained elements.
    """
    if obj.internal_reference_no:
        return obj.internal_reference_no
    return _marker


@indexer(IDmsIncomingMail)
def im_external_reference_number_indexer(obj):
    """Indexer of 'external_reference_number' for IDmsIncomingMail. Stores external_reference_no.
    Specific indexer method to avoid acquisition of dmsincomingmail contained elements.
    """
    if obj.external_reference_no:
        return obj.external_reference_no
    return _marker


@indexer(IDmsOutgoingMail)
def om_external_reference_number_indexer(obj):
    """Indexer of 'external_reference_number' for IDmsOutgoingMail. Stores external_reference_no.
    Specific indexer method to avoid acquisition of dmsoutgoingmail contained elements.
    """
    if obj.external_reference_no:
        return obj.external_reference_no
    return _marker


def add_parent_organizations(obj, index):
    for org in obj.get_organizations_chain():
        index.append('l:%s' % org.UID())


def relations_index(obj, attr):
    if not base_hasattr(obj, attr):
        return _marker
    value = getattr(obj, attr)
    if not value:
        return _marker
    index = []
    if not isinstance(value, list):
        value = [value]
    for rel in value:
        if rel.isBroken():
            continue
        related = rel.to_object
        index.append(related.UID())

        if related.portal_type == 'organization':
            add_parent_organizations(related, index)
        elif related.portal_type == 'held_position':
            add_parent_organizations(related.get_organization(), index)
    if index:
        # make unique items
        return list(set(index))
    return _marker


@indexer(IDmsDocument)
def sender_index(obj):
    """Indexer of 'sender_index' for IDmsDocument

    Stores:
        * the sender UIDs
        * the organizations chain UIDs if the sender is an organization or a held position, prefixed by 'l:'
    """
    return relations_index(obj, 'sender')


@indexer(IDmsDocument)
def recipients_index(obj):
    """Indexer of 'recipients_index' for IDmsDocument

    Stores:
        * the recipient UIDs
        * the organizations chain UIDs if the recipient is an organization or a held position, prefixed by 'l:'
    """
    return relations_index(obj, 'recipients')
