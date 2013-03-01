# -*- coding: utf8 -*-

from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
import collective.dms.mailcontent

COLLECTIVE_DMS_MAILCONTENT = PloneWithPackageLayer(
    zcml_package=collective.dms.mailcontent,
    zcml_filename='testing.zcml',
    additional_z2_products=(),
    gs_profile_id='collective.dms.mailcontent:testing',
    name="COLLECTIVE_DMS_MAILCONTENT")

INTEGRATION = IntegrationTesting(
    bases=(COLLECTIVE_DMS_MAILCONTENT, ),
    name="INTEGRATION")

FUNCTIONAL = FunctionalTesting(
    bases=(COLLECTIVE_DMS_MAILCONTENT, ),
    name="FUNCTIONAL")
