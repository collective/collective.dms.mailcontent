"""Module functions of the package __init__."""

from collective.dms.mailcontent import _tr
from collective.dms.mailcontent.testing import INTEGRATION
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import unittest


class TestInit(unittest.TestCase):

    layer = INTEGRATION

    def setUp(self):
        self.portal = self.layer["portal"]

    def test__tr(self):
        # translated in the site default language, whatever the request language
        # Plone 6: registry record plone.default_language (Plone 4: site_properties default_language)
        self.assertEqual(api.portal.get_registry_record("plone.default_language"), "en")
        self.assertEqual(
            _tr("(dmsmainfile) => ${title}", mapping={"title": "D1"}),
            "(dmsmainfile) => D1",
        )
        api.portal.set_registry_record("plone.default_language", "fr")
        self.assertEqual(
            _tr("(dmsmainfile) => ${title}", mapping={"title": "D1"}), "(V) => D1"
        )
        self.assertEqual(
            _tr("Reply to ${ref}", mapping={"ref": "in/1"}), "R\xe9pondre \xe0 in/1"
        )
        # another domain
        self.assertEqual(_tr("Save", domain="plone"), "Enregistrer")
        # French without the record
        del getUtility(IRegistry).records["plone.default_language"]
        self.assertEqual(
            _tr("(dmsmainfile) => ${title}", mapping={"title": "D1"}), "(V) => D1"
        )
