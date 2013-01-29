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

    def test_reception_date_default_value(self):
        data = dmsmail.DmsIncomingMail()
        self.assertEqual(dmsmail.receptionDateDefaultValue(data), datetime.date.today())

    def test_original_date_default_value(self):
        data = dmsmail.DmsIncomingMail()
        self.assertEqual(dmsmail.originalMailDateDefaultValue(data), datetime.date.today()-datetime.timedelta(3))