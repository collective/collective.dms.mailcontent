# -*- coding: utf-8 -*-
from datetime import date, datetime, time
import logging

from plone import api

from Products.contentmigration.field import migrateField

logger = logging.getLogger('collective.dms.mailcontent: upgrade. ')


def v2(context):
    default_time = time(10, 0)
    catalog = api.portal.get_tool('portal_catalog')
    brains = catalog.searchResults({'portal_type': 'dmsincomingmail'})
    for brain in brains:
        obj = brain.getObject()
        reception_date = obj.reception_date
        if isinstance(reception_date, date):
            obj.reception_date = datetime.combine(reception_date, default_time)


def v3(context):
    catalog = api.portal.get_tool('portal_catalog')
    setup = api.portal.get_tool('portal_setup')
    setup.runAllImportStepsFromProfile('profile-collective.dms.mailcontent:default')
    brains = catalog.searchResults({'portal_type': 'dmsincomingmail'})
    for brain in brains:
        obj = brain.getObject()
        obj.reindexObject(idxs=('Title', 'SearchableText', 'sortable_title'))


def v4(context):
    setup = api.portal.get_tool('portal_setup')
    setup.runImportStepFromProfile('profile-collective.dms.mailcontent:default', 'typeinfo')
    catalog = api.portal.get_tool('portal_catalog')
    migrated = False
    for brain in catalog.searchResults(portal_type=['dmsincomingmail', 'dmsoutgoingmail']):
        obj = brain.getObject()
        if migrateField(obj, {'fieldName': 'in_reply_to', 'newFieldName': 'reply_to'}):
            migrated = True
    logger.info("%s object fields were migrated" % (migrated and 'Some' or 'None'))


def v5(context):
    setup = api.portal.get_tool('portal_setup')
    setup.runImportStepFromProfile('profile-collective.dms.mailcontent:default', 'catalog')
    catalog = api.portal.get_tool('portal_catalog')
    nb = 0
    for brain in catalog.searchResults(portal_type=['dmsincomingmail', 'dmsoutgoingmail']):
        nb += 1
        obj = brain.getObject()
        obj.reindexObject(idxs=['sender'])
    logger.info("%d objects were migrated" % nb)


def v6(context):
    setup = api.portal.get_tool('portal_setup')
    setup.runImportStepFromProfile('profile-collective.dms.mailcontent:default', 'catalog')
    setup.runImportStepFromProfile('profile-collective.dms.mailcontent:default', 'plone.app.registry')
    catalog = api.portal.get_tool('portal_catalog')
    nb = 0
    for brain in catalog.searchResults(portal_type=['dmsincomingmail', 'dmsoutgoingmail']):
        nb += 1
        obj = brain.getObject()
        obj.reindexObject(idxs=['recipients'])
    logger.info("%d objects were migrated" % nb)


def v7(context):
    catalog = api.portal.get_tool('portal_catalog')
    nb = 0
    for brain in catalog.searchResults(portal_type=['dmsincomingmail']):
        nb += 1
        obj = brain.getObject()
        sender = obj.sender
        if sender and not isinstance(sender, list):
            obj.sender = [sender]
            obj.reindexObject(idxs=['sender_index'])
    logger.info("%d objects were migrated" % nb)


def v8(context):
    """ Avoid warning about unresolved dependencies """
    setup = api.portal.get_tool('portal_setup')
    step = 'dmsmailcontent-postInstall'
    registry = setup.getImportStepRegistry()
    registry._registered.get(step)['dependencies'] = (u'catalog', u'controlpanel', u'plone.app.registry', u'rolemap',
                                                      u'typeinfo')
    setup._p_changed = True
    logger.info("Import step dependency corrected")


def v10(context):
    """ Upgrade indexes """
    setup = api.portal.get_tool('portal_setup')
    setup.runImportStepFromProfile('profile-collective.dms.mailcontent:default', 'catalog')
    catalog = api.portal.get_tool('portal_catalog')
    catalog.manage_reindexIndex(ids=['sender_index', 'recipients_index'])
    logger.info("Catalog updated")
