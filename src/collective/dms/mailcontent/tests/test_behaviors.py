from collective.dms.mailcontent.behaviors import ISendingType
from collective.dms.mailcontent.behaviors import sending_types
from collective.dms.mailcontent.testing import INTEGRATION
from ecreall.helpers.testing.base import BaseTest
from plone.app.testing.helpers import setRoles
from plone.app.testing.interfaces import TEST_USER_ID
from plone.app.testing.interfaces import TEST_USER_NAME
from plone.autoform.interfaces import IFormFieldProvider
from plone.behavior.interfaces import IBehavior
from z3c.form.browser.radio import RadioWidget
from zope.component import getUtility
from zope.i18n import translate

import unittest


class TestBehaviors(unittest.TestCase, BaseTest):
    """Tests behaviors"""

    layer = INTEGRATION

    def setUp(self):
        super().setUp()
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.login(TEST_USER_NAME)
        self.portal.invokeFactory("testtype", "testitem")
        self.testitem = self.portal["testitem"]

    def test_behaviors_installation(self):
        sending_type_behavior = getUtility(
            IBehavior, name="collective.dms.mailcontent.behaviors.ISendingType"
        )
        self.assertEqual(sending_type_behavior.interface, ISendingType)
        self.assertTrue(IFormFieldProvider.providedBy(sending_type_behavior.interface))
        self.assertEqual(sending_type_behavior.title, "SendingType")
        self.assertEqual(sending_type_behavior.description, "Sending type behavior")

    def test_sending_type_fields(self):
        item = self.testitem
        # Plone 6: master's "assertIsNone(item.getAttributes())" dropped: nothing named so is acquired any more
        # (Plone 4: None, not related to the behavior)
        self.assertTrue(hasattr(item, "sending_type"))
        self.assertEqual(item.sending_type, "normal")
        item.sending_type = "registered"
        self.assertEqual(item.sending_type, "registered")
        self.assertFalse(ISendingType["sending_type"].required)
        # the add form proposes the sending types as radio buttons, "normal" checked
        form = self.portal.restrictedTraverse("++add++testtype").form_instance
        form.update()
        widget = form.widgets["ISendingType.sending_type"]
        self.assertIsInstance(widget, RadioWidget)
        self.assertEqual(widget.value, ["normal"])
        self.assertEqual(
            [(i["value"], i["checked"]) for i in widget.items],
            [("normal", True), ("registered", False)],
        )

    def test_sending_types(self):
        self.assertEqual(
            [(t.value, t.token, translate(t.title)) for t in sending_types],
            [
                ("normal", "normal", "Normal"),
                ("registered", "registered", "Registered"),
            ],
        )
        self.assertEqual(
            [translate(t.title, target_language="fr") for t in sending_types],
            ["Normal", "Par recommand\xe9"],  # codespell:ignore recommand
        )
