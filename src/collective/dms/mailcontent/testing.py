# -*- coding: utf8 -*-

from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from zope.globalrequest.local import setLocal

import collective.dms.mailcontent


class MailcontentLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base layer.
        self.loadZCML(package=collective.dms.mailcontent, name="testing.zcml")

    def setUpPloneSite(self, portal):
        setLocal("request", portal.REQUEST)  # to avoid error with empty request in P6
        applyProfile(portal, "collective.dms.mailcontent:testing")
        # setRoles(portal, TEST_USER_ID, ["Manager"])


COLLECTIVE_DMS_MAILCONTENT = MailcontentLayer()

INTEGRATION = IntegrationTesting(bases=(COLLECTIVE_DMS_MAILCONTENT,), name="INTEGRATION")

FUNCTIONAL = FunctionalTesting(bases=(COLLECTIVE_DMS_MAILCONTENT,), name="FUNCTIONAL")
