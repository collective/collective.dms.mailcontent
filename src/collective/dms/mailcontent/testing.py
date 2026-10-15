from plone import api
from plone.app.dexterity.textindexer.indexer import dynamic_searchable_text_indexer
from plone.app.robotframework.content import Content
from plone.app.robotframework.remote import RemoteLibraryLayer
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.robotframework.utils import disableCSRFProtection
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedBlobImage
from plone.testing.zope import WSGI_SERVER_FIXTURE
from zope.component import provideAdapter
from zope.globalrequest.local import setLocal

import collective.dms.mailcontent
import collective.iconifiedcategory
import os
import transaction


class MailcontentLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base layer.
        self.loadZCML(package=collective.dms.mailcontent, name="testing.zcml")
        # the text indexer is registered below this layer (PLONE_FIXTURE), where basecontent's SearchableText
        # indexer would win whatever the behaviors: registered again here, as it wins in an instance
        provideAdapter(dynamic_searchable_text_indexer, name="SearchableText")

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
        icon_path = os.path.join(
            os.path.dirname(collective.iconifiedcategory.__file__),
            "tests",
            "icône1.png",
        )
        with open(icon_path, "rb") as fl:
            api.content.create(
                type="ContentCategory",
                title="To sign",
                container=category_group,
                icon=NamedBlobImage(fl.read(), filename="icône1.png"),
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
        # the indexing queue (image scales need the registry) must run before the layer unsets the site
        transaction.commit()
        setLocal("request", None)


COLLECTIVE_DMS_MAILCONTENT = MailcontentLayer()

INTEGRATION = IntegrationTesting(
    bases=(COLLECTIVE_DMS_MAILCONTENT,), name="INTEGRATION"
)

FUNCTIONAL = FunctionalTesting(bases=(COLLECTIVE_DMS_MAILCONTENT,), name="FUNCTIONAL")


class MailcontentAcceptanceLayer(PloneSandboxLayer):
    """Robot data: contacts of the collective.contact.core test_data profile, a site admin and an agent"""

    defaultBases = (COLLECTIVE_DMS_MAILCONTENT,)

    def setUpPloneSite(self, portal):
        setLocal("request", portal.REQUEST)
        applyProfile(portal, "collective.contact.core:test_data")
        api.user.create(
            email="siteadmin@example.com", username="siteadmin", password="SiteAdm!n0"
        )
        api.group.add_user(groupname="Administrators", username="siteadmin")
        # adds and edits mails without being Manager or Site Administrator (irn hidden by the settings)
        api.user.create(
            email="agent@example.com",
            username="agent",
            password="Agent!1234",
            roles=["Contributor", "Editor"],
        )
        # the indexing queue (image scales of the test_data photos) must run before the layer unsets the site
        transaction.commit()
        setLocal("request", None)


ACCEPTANCE_FIXTURE = MailcontentAcceptanceLayer(name="ACCEPTANCE_FIXTURE")


class CSRFSafeContent(Content):
    """Set field value is aborted by plone.protect on Plone 6 otherwise (Create content disables the check)"""

    def set_field_value(self, uid, field, value, field_type):
        disableCSRFProtection()
        return super().set_field_value(uid, field, value, field_type)


REMOTE_LIBRARY_FIXTURE = RemoteLibraryLayer(
    bases=(PLONE_FIXTURE,),
    libraries=tuple(
        CSRFSafeContent if lib is Content else lib
        for lib in REMOTE_LIBRARY_BUNDLE_FIXTURE.libraryBases[1:]
    ),
    name="RemoteLibraryBundle:RobotRemote",
)

ACCEPTANCE = FunctionalTesting(
    bases=(ACCEPTANCE_FIXTURE, REMOTE_LIBRARY_FIXTURE, WSGI_SERVER_FIXTURE),
    name="ACCEPTANCE",
)
