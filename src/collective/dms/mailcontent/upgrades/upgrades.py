# -*- coding: utf-8 -*-
from plone import api

import logging
import os
import transaction


logger = logging.getLogger("collective.dms.mailcontent: upgrade. ")


def v11(context):
    setup = api.portal.get_tool("portal_setup")
    setup.runImportStepFromProfile("profile-collective.dms.mailcontent:default", "catalog")
    catalog = api.portal.get_tool("portal_catalog")
    nb = 0
    commit_value = int(os.getenv("COMMIT", "0"))
    for brain in catalog.searchResults(portal_type=["dmsincomingmail", "dmsoutgoingmail"]):
        nb += 1
        obj = brain.getObject()
        obj.reindexObject(idxs=["external_reference_number"])
        if commit_value and nb % commit_value == 0:
            transaction.commit()
            logger.info("On mailcontent commit {}".format(nb))
    logger.info("%d objects were migrated" % nb)
