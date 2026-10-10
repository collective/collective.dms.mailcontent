#! -*- coding: utf8 -*-

from setuptools import find_packages
from setuptools import setup


version = "2.0.0.dev0"

long_description = (
    open("README.rst").read() + "\n" + "Contributors\n"
    "============\n" + "\n" + open("CONTRIBUTORS.rst").read() + "\n" + open("CHANGES.rst").read() + "\n"
)

setup(
    name="collective.dms.mailcontent",
    version=version,
    description="Mail content type for document management system",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.2",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="document management system dms mail",
    author="Ecreall, Entrouvert, IMIO",
    author_email="cedricmessiant@ecreall.com",
    url="https://github.com/collective/collective.dms.mailcontent",
    download_url="https://pypi.org/project/collective.dms.mailcontent",
    license="gpl",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "setuptools",
        "plone.api",
        "plone.app.dexterity",
        "collective.contact.core",
        "collective.contact.widget",
        "collective.dms.basecontent>1.99",
        "imio.helpers>=0.55",
        "plone.app.relationfield",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            "plone.app.robotframework",
            "robotsuite",
            "ecreall.helpers.testing",
        ],
    },
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
