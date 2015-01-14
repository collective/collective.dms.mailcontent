# -*- coding: utf-8 -*-
from datetime import date, datetime, time

from plone import api


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
        obj.reindexObject(idxs=('Title', 'SearchableText'))
