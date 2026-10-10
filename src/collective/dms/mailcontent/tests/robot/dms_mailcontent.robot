*** Settings ***
Documentation  collective.dms.mailcontent keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Fixture (testing.py, ACCEPTANCE): testing profile (next numbers 10, expressions
...            python:'test-in/'+number and python:'test-out/'+number), contacts of the collective.contact.core
...            test_data profile (mydirectory), user siteadmin (Administrators), user agent (Contributor, Editor).
Resource  ui_plone${PLONE_MAJOR}.robot
Library  DateTime


*** Variables ***
${SITE_ADMIN}  siteadmin
${SITE_ADMIN_PASSWORD}  SiteAdm!n0
${AGENT}  agent
${AGENT_PASSWORD}  Agent!1234
${DIRECTORY_URL}  ${PLONE_URL}/mydirectory
${MAILS_URL}  ${PLONE_URL}/mails


*** Keywords ***
Log in as site admin
    Log in with the login form  ${SITE_ADMIN}  ${SITE_ADMIN_PASSWORD}

Log in as agent
    Log in with the login form  ${AGENT}  ${AGENT_PASSWORD}

Today
    [Arguments]  ${increment}=0
    ${date} =  Get current date  increment=${increment}  result_format=%Y-%m-%d
    [Return]  ${date}

Create the mails folder
    [Documentation]  Folder /mails (a manager autologin is enabled: log in afterwards)
    Enable autologin as  Manager
    ${uid} =  Create content  type=Folder  id=mails  title=Mails
    [Return]  ${uid}

Create an incoming mail
    [Documentation]  In the mails folder, sent by a contact of mydirectory; its internal reference number
    ...              is given at creation (next number of the settings)
    [Arguments]  ${id}  ${title}  ${sender}=rambo  ${treating_group}=Reviewers
    Enable autologin as  Manager
    ${folder_uid} =  Path to uid  /plone/mails
    ${sender_uid} =  Path to uid  /plone/mydirectory/${sender}
    ${uid} =  Create content  type=dmsincomingmail  container=${folder_uid}  id=${id}  title=${title}
    ...  external_reference_no=EXT-${id}
    Set field value  ${uid}  sender  ["${sender_uid}"]  references
    Set field value  ${uid}  treating_groups  ["${treating_group}"]  list
    [Return]  ${uid}

Create an outgoing mail
    [Documentation]  In the mails folder, sent to a contact of mydirectory
    [Arguments]  ${id}  ${title}  ${recipient}=draper
    Enable autologin as  Manager
    ${folder_uid} =  Path to uid  /plone/mails
    ${recipient_uid} =  Path to uid  /plone/mydirectory/${recipient}
    ${uid} =  Create content  type=dmsoutgoingmail  container=${folder_uid}  id=${id}  title=${title}
    Set field value  ${uid}  recipients  ["${recipient_uid}"]  references
    [Return]  ${uid}

Open the incoming mail add form
    Go to  ${PLONE_URL}
    Click the add menu item  dmsincomingmail

Open the outgoing mail add form
    Go to  ${PLONE_URL}
    Click the add menu item  dmsoutgoingmail

Open the outgoing mail edit form
    [Documentation]  Edit form of the outgoing mails (OMEdit, @@dmsdocument-edit)
    [Arguments]  ${url}
    Go to  ${url}/@@dmsdocument-edit

Fill the title
    [Arguments]  ${title}
    Input text  css=#form-widgets-IDublinCore-title  ${title}

The page title is
    [Documentation]  Heading of a content view
    [Arguments]  ${title}
    Element text should be  css=#content h1  ${title}

The page title contains
    [Documentation]  Heading of a content view or a form
    [Arguments]  ${text}
    Element should contain  css=#content h1  ${text}

The text field shows
    [Documentation]  Value of a text input of a form
    [Arguments]  ${field_name}  ${value}
    Textfield value should be  css=#form-widgets-${field_name}  ${value}

Fill the text field
    [Arguments]  ${field_name}  ${value}
    Input text  css=#form-widgets-${field_name}  ${value}

The radio field is set to
    [Documentation]  Checked value (token) of a radio widget
    [Arguments]  ${field_name}  ${value}
    Radio button should be set to  form.widgets.${field_name}  ${value}

Select in the radio field
    [Arguments]  ${field_name}  ${value}
    Select radio button  form.widgets.${field_name}  ${value}

The internal reference number field shows
    [Arguments]  ${value}
    Element should be visible  css=label[for="form-widgets-internal_reference_no"]
    Element should be visible  css=#form-widgets-internal_reference_no
    Textfield value should be  css=#form-widgets-internal_reference_no  ${value}

The internal reference number field is hidden
    [Documentation]  Hidden input without label (the field wrapper stays)
    Element should not be visible  css=#form-widgets-internal_reference_no
    Page should not contain element  css=label[for="form-widgets-internal_reference_no"]

Fill the internal reference number
    [Arguments]  ${value}
    Input text  css=#form-widgets-internal_reference_no  ${value}

The internal reference number field starts with
    [Arguments]  ${prefix}
    ${value} =  Get value  css=#form-widgets-internal_reference_no
    Should start with  ${value}  ${prefix}

The field shows
    [Documentation]  Field of a display form (content view)
    [Arguments]  ${field_name}  ${text}
    Element should contain  css=#form-widgets-${field_name}  ${text}

The field links to
    [Documentation]  Link of a relation or contact field of a display form (content view)
    [Arguments]  ${field_name}  ${url}  ${text}
    Element should contain  xpath=//*[@id="form-widgets-${field_name}"]//a[@href="${url}"]  ${text}

The contact is selected in the widget
    [Documentation]  The contact (by url) is checked in the contact widget (collective.contact.widget templates)
    [Arguments]  ${field_name}  ${url}
    ${input} =  Set variable  xpath=//*[@id="form-widgets-${field_name}-input-fields"]//label[.//a[@href="${url}"]]/input
    Wait until page contains element  ${input}
    Checkbox should be selected  ${input}

Open the settings
    [Documentation]  Dms Mail settings, from the Site Setup
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click the control panel link  Dms Mail settings
    Location should be  ${PLONE_URL}/@@dmsmailcontent-settings

Change the outgoing mail settings
    [Documentation]  edit_irn: label of the "Internal reference number edition field" choice
    [Arguments]  ${edit_irn}=Always show  ${increment}=${True}  ${today}=${True}
    Open the settings
    Click the form tab  Outgoing mail
    Select in the selection widget  outgoingmail_edit_irn  ${edit_irn}
    Set the single checkbox widget  outgoingmail_increment_number  ${increment}
    Set the single checkbox widget  outgoingmail_today_mail_date  ${today}
    Save the form
    The status message contains  Changes saved
