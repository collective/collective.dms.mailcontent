"""Robot suites of tests/robot, run with the layer of their file name.

ROBOT_PLONE_MAJOR selects the UI keywords (ui_plone6.robot): robotsuite passes the
ROBOT_* environment variables to the suites as robot variables.
"""

from collective.dms.mailcontent.testing import ACCEPTANCE
from importlib.metadata import version
from plone.app.testing import ROBOT_TEST_LEVEL
from plone.testing import layered

import os
import robotsuite
import unittest

# suites needing an optional integration layer, e.g. {'test_facetednav.robot': ADDONS_ACCEPTANCE}
SUITE_LAYERS = {}
# scenarios pinning a Plone 4 bug still there (MIGRATION.md Known issues): expected failures (noncritical on the
# Robot Framework 3 of Plone 4; Robot Framework 4+ has no criticality): an unexpected success fails the run
EXPECTED_FAILURE_TAGS = {"plone4-bug"}


def test_suite():
    os.environ.setdefault(
        "ROBOT_PLONE_MAJOR", version("Products.CMFPlone").split(".")[0]
    )
    suite = unittest.TestSuite()
    robot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robot")
    for name in sorted(os.listdir(robot_dir)):
        if name.startswith("test_") and name.endswith(".robot"):
            robot_suite = robotsuite.RobotTestSuite(os.path.join("robot", name))
            for test in robot_suite:
                if EXPECTED_FAILURE_TAGS.intersection(test._tags):
                    test.__unittest_expecting_failure__ = True
            # not run by a plain bin/test: bin/test --all -t robot
            robot_suite.level = ROBOT_TEST_LEVEL
            suite.addTests(
                [layered(robot_suite, layer=SUITE_LAYERS.get(name, ACCEPTANCE))]
            )
    return suite
