Changelog
=========

0.3 (unreleased)
----------------

- Nothing changed yet.


0.2 (2015-06-02)
----------------

- Use current datetime as encoding datetime [sgeulette]


0.1.8 (2015-01-14)
------------------

- Added internal reference number in Title and in SearchableText [sgeulette]


0.1.7 (2014-11-26)
------------------

- Corrected bad index name [sgeulette]


0.1.6 (2014-04-04)
------------------

- Removed Member from add permission. Must be the default. [sgeulette]


0.1.5 (2014-03-04)
------------------

- Add recipients field for incomingmail [cedricmessiant]
- Add ISendingType behaviour [cedricmessiant]
- Add indexer for in_reply_to field [cedricmessiant]
- Updated testing infra [vincentfretin]
- Make reception date a datetime [cedricmessiant]


0.1.4 (2013-04-24)
------------------

- Manage internal_reference field automatically (no user input needed) [sgeulette]
- Add good proposal value in validation error message [sgeulette]
- Update validateIndexValueUniqueness: skip empty value [sgeulette]
- Use plone.formwidget.datetime [cedricmessiant]
- Allow tasks to be added to mails [fredericpeters]


0.1.3 (2013-03-12)
------------------

- Change the index name and definition to avoid bad index on mail contained elements. Add a specific method linked to the index.
  [sgeulette]


0.1.2 (2013-03-08)
------------------

- Corrected MANIFEST.in


0.1.1 (2013-03-07)
------------------

- Added missing file in egg


0.1 (2013-03-06)
----------------

- Package created using templer
  [cedricmessiant]
- Mail types
  [fredericpeters]
- Related docs
  [davidconvent]
- Translations, icons
  [sgeulette]
- Default values, expression evaluation
  [sgeulette]
- Setting forms
  [sgeulette]
- Tests
  [sgeulette]
