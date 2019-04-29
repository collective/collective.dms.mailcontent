Changelog
=========

1.5 (unreleased)
----------------

- Use a separated method to update reply fields (reused in batchactions form)
  [sgeulette]

1.4 (2019-04-26)
----------------

- Renamed sender and recipients indexes.
  [sgeulette]

1.3 (2019-03-12)
----------------

- Added settings to manage internal_reference_no field visibility and
  number incrementing for outgoing mails.
  [sgeulette]
- Added reply view to respond to incoming mail.
  [sgeulette]
- Added external_reference_no in outgoing mail.
  [sgeulette]
- Removed some grok
  [sgeulette]

1.2.1 (2018-10-18)
------------------

- Corrected empty dependency step causing unresolved warning. Save changes !
  [sgeulette]

1.2 (2018-10-11)
----------------

- Corrected empty dependency step causing unresolved warning.
  [sgeulette]

1.1 (2018-07-23)
----------------

- Changed sender field from ContactChoice to ContactList (multiple values).
  [sgeulette]
- Some corrections on encoding and index update
  [sgeulette]

1.0 (2017-05-30)
----------------

- Add a recipients index, containing also the organisation chain UIDs [sgeulette]
- Updated reply_to field to allow dmsincomingmail and dmsoutgoingmail types. [sgeulette]
- Corrected indexer not working with 2 decorators. [sgeulette]
- Added display_backrefs on reply_to field. [sgeulette]
- Combined title and internal_reference_no in Title for OutgoingMail [sgeulette]
- Set internal_reference_no if empty [sgeulette]
- Add internal_reference_no in SearchableText [sgeulette]
- Display time on reception_date [sgeulette]
- Added option to set outgoing mail date at today [sgeulette]

0.5 (2016-04-15)
----------------

- Add a sender index, containing also the organisation chain UIDs [sgeulette]
- Add a sender_index metadata [sgeulette]
- Use the same permission to protect config view and configlet. [sgeulette]

0.4 (2016-01-05)
----------------

- Set original_mail_date as not required. [sgeulette]

0.3 (2015-11-24)
----------------

- Give access to configlet to Site Administrator [sgeulette].
- Renamed 'in_reply_to' field to avoid child index interference with plone.app.discussion [sgeulette]
- Updated buildout [sgeulette]
- Avoid None in internal_reference_number index. ZCatalog 3 compatibility. [sgeulette]
- Set original_mail_date as required. Added default value [sgeulette]

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
