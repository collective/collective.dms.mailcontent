"""browser/utils.py"""

from collective.dms.mailcontent.browser.utils import UtilsMethods
from collective.dms.mailcontent.testing import INTEGRATION
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestUtilsMethods(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.folder = api.content.create(
            container=self.portal, type="Folder", id="folder", title="Folder"
        )
        self.im = api.content.create(
            container=self.folder, type="dmsincomingmail", id="im", title="I mail"
        )
        self.om = api.content.create(
            container=self.folder, type="dmsoutgoingmail", id="om", title="O mail"
        )

    def test_outgoingmail_folder(self):
        view = self.im.restrictedTraverse("@@cdmc-utils")
        self.assertIsInstance(view, UtilsMethods)
        # the reply of an incoming mail is created next to it
        self.assertEqual(view.outgoingmail_folder(), self.folder)
        # elsewhere in the context
        self.assertEqual(
            self.folder.restrictedTraverse("@@cdmc-utils").outgoingmail_folder(),
            self.folder,
        )
        self.assertEqual(
            self.om.restrictedTraverse("@@cdmc-utils").outgoingmail_folder(), self.om
        )
        # allowed attribute, usable by a member in a TAL path
        setRoles(self.portal, TEST_USER_ID, ["Member"])
        self.assertEqual(
            self.im.restrictedTraverse("@@cdmc-utils/outgoingmail_folder")(),
            self.folder,
        )
