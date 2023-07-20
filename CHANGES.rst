Changelog
=========

1.13 (2023-07-20)
-----------------

- Added range (min and max) on fields original_mail_date and reception_date.
  [bleybaert]

1.12 (2022-12-12)
-----------------

- Added intermediate commit option in v11 upgrade
  [sgeulette]

1.11 (2022-10-28)
-----------------

- Added `DmsOutgoingMail.get_replied` to get the linked incoming mail.
  [sgeulette]

1.10 (2022-08-19)
-----------------

- Improved EmailAttachmentsVocabulary to escape mailing document and dmsfile filename title.
  [sgeulette]

1.9 (2022-03-25)
----------------

- When listing attachments, do not include filename if it's the same than title.
  [sgeulette]
- Marked signed attachment
  [sgeulette]

1.8 (2022-03-17)
----------------

- Made separate `add_content` method to be overrided.
  [sgeulette]

1.7 (2022-02-10)
----------------

- Corrected contact imports after code move.
  [sgeulette]
- Corrected and improved EmailAttachmentsVocabulary
  [sgeulette]

1.6.1 (2021-12-10)
------------------

- Avoided error in reply_form during masterselect widget call.
  [sgeulette]

1.6 (2021-12-06)
----------------

- Added in EmailAttachmentsVocabulary related files of linked mails (reply_to)
  [sgeulette]
- Improved reply form to initialize reply_to widget with incomingmail reply_to values
  (including backrefs). Do not include deeper refs.
  [sgeulette]

1.5 (2021-04-20)
----------------

- Use interface to ckeck context in validateIndexValueUniqueness
  (multiple types can use the same interface).
  [sgeulette]
- RelatedDocs field (reply_to) use now object_provides criteria
  [sgeulette]
- Replaced portal_type test by schema interface providedBy test
  [sgeulette]
- Added IOutgoingEmail and IFieldsetOutgoingEmail schema interfaces to describe
  email information
  [sgeulette]
- Added external_reference_number index
  [sgeulette]

1.4.3 (2020-10-07)
------------------

- Reply form: added im treating_groups in om recipient_groups if another group responds
  [sgeulette]
- Added tests on reply form
  [sgeulette]

1.4.2 (2019-05-09)
------------------

- Correction when setting form values: no more change after form edition.
  [sgeulette]

1.4.1 (2019-04-29)
------------------

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
