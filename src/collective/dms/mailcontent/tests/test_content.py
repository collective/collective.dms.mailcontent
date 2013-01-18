# -*- coding: utf8 -*-

import unittest2 as unittest
import datetime

from plone.app.testing import setRoles, TEST_USER_ID
from collective.dms.mailcontent.testing import INTEGRATION
from collective.dms.mailcontent import dmsmail

class TestContentTypes(unittest.TestCase):
    """Base class to test new content types"""

    layer = INTEGRATION

    def setUp(self):
        super(TestContentTypes, self).setUp()
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])


class TestDmsIncomingMail(TestContentTypes):

    def test_reception_default_value(self):
        data = dmsmail.DmsIncomingMail()
        self.assertEqual(dmsmail.receptionDefaultValue(data), datetime.date.today())
