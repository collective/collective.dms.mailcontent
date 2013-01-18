# -*- coding: utf8 -*-

from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

import collective.dms.mailcontent

class MailContentLayer(PloneWithPackageLayer):

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'collective.dms.mailcontent:default')


COLLECTIVE_DMS_MAILCONTENT = MailContentLayer(
    zcml_package=collective.dms.mailcontent,
    zcml_filename='configure.zcml',
    gs_profile_id='collective.dms.mailcontent:default',
    name="COLLECTIVE_DMS_MAILCONTENT")

INTEGRATION = IntegrationTesting(
    bases=(COLLECTIVE_DMS_MAILCONTENT, ),
    name="INTEGRATION")

FUNCTIONAL = FunctionalTesting(
    bases=(COLLECTIVE_DMS_MAILCONTENT, ),
    name="FUNCTIONAL")
