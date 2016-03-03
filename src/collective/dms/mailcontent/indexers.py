from plone.indexer import indexer

from Products.PluginIndexes.common.UnIndex import _marker

from collective.dms.mailcontent.dmsmail import IDmsIncomingMail, IDmsOutgoingMail


@indexer(IDmsIncomingMail)
@indexer(IDmsOutgoingMail)
def sender_index(obj):
    """
        return an index containing:
        * the sender UID
        * the organizations chain UIDs if the sender is an organization or a held position, prefixed by 'l:'
    """
    # we check the stored value that must contain a z3c.relationfield.relation.RelationValue object
    if not obj.sender or obj.sender.isBroken():
        return _marker
    index = [obj.sender.to_object.UID()]

    def add_parent_organizations(obj, index):
        for org in obj.get_organizations_chain():
            index.append('l:%s' % org.UID())

    if obj.sender.to_object.portal_type == 'organization':
        add_parent_organizations(obj.sender.to_object, index)
    elif obj.sender.to_object.portal_type == 'held_position':
        add_parent_organizations(obj.sender.to_object.get_organization(), index)
    return index
