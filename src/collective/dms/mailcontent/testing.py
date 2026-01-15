# -*- coding: utf8 -*-
from plone import api
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedBlobImage
from zope.globalrequest.local import setLocal

import collective.dms.mailcontent
import collective.iconifiedcategory
import os


class MailcontentLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base layer.
        self.loadZCML(package=collective.dms.mailcontent, name="testing.zcml")

    def setUpPloneSite(self, portal):
        setLocal("request", portal.REQUEST)  # to avoid error with empty request in P6
        applyProfile(portal, "collective.dms.mailcontent:testing")
        setRoles(portal, TEST_USER_ID, ["Manager"])
        at_folder = api.content.create(
            container=portal,
            id="annexes_types",
            title="Annexes Types",
            type="ContentCategoryConfiguration",
            exclude_from_nav=True,
        )
        category_group = api.content.create(
            type="ContentCategoryGroup",
            title="Annexes",
            container=at_folder,
            id="annexes",
        )
        icon_path = os.path.join(os.path.dirname(collective.iconifiedcategory.__file__), "tests", "icône1.png")
        with open(icon_path, "rb") as fl:
            api.content.create(
                type="ContentCategory",
                title="To sign",
                container=category_group,
                icon=NamedBlobImage(fl.read(), filename=u"icône1.png"),
                id="to_sign",
                predefined_title="To be signed",
                # confidential=True,
                # to_print=True,
                to_sign=True,
                # signed=True,
                # publishable=True,
                # only_pdf=True,
                show_preview=False,
            )


COLLECTIVE_DMS_MAILCONTENT = MailcontentLayer()

INTEGRATION = IntegrationTesting(bases=(COLLECTIVE_DMS_MAILCONTENT,), name="INTEGRATION")

FUNCTIONAL = FunctionalTesting(bases=(COLLECTIVE_DMS_MAILCONTENT,), name="FUNCTIONAL")
