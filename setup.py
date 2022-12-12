#! -*- coding: utf8 -*-

from setuptools import setup, find_packages

version = '1.12'

long_description = (
    open('README.rst').read()
    + '\n' +
    'Contributors\n'
    '============\n'
    + '\n' +
    open('CONTRIBUTORS.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')

setup(
    name='collective.dms.mailcontent',
    version=version,
    description="Mail content type for document management system",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.2",
        "Framework :: Plone :: 4.3",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='document management system dms mail',
    author='Ecreall, Entrouvert, IMIO',
    author_email='cedricmessiant@ecreall.com',
    url='https://github.com/collective/collective.dms.mailcontent',
    download_url='https://pypi.org/project/collective.dms.mailcontent',
    license='gpl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['collective', 'collective.dms'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Products.contentmigration',
        'setuptools',
        'plone.api',
        'plone.app.dexterity',
        'plone.directives.form',
        'collective.contact.core',
        'collective.dexteritytextindexer',
        'collective.dms.basecontent',
        'imio.helpers>=0.55',
        'plone.formwidget.datetime',
        #'plone.app.relationfield',
        'five.grok',
    ],
    extras_require={
        'test': ['plone.app.testing',
                 'unittest2',
                 'ecreall.helpers.testing',
                 ],
    },
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
