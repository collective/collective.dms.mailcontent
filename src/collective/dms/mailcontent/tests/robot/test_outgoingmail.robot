*** Settings ***
Documentation  The outgoing mail: add form (default mail date and internal reference number, required
...            recipients), edit form (@@dmsdocument-edit), uniqueness of the internal reference number,
...            internal reference number hidden or shown by the settings for a user who is not an administrator.
Resource  dms_mailcontent.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
Add an outgoing mail
    Log in as site admin
    Open the outgoing mail add form
    ${today} =  Today
    The date widget value is  mail_date  ${today}
    The internal reference number field shows  test-out/10
    Fill the title  Answer
    Save the form
    The field error contains  recipients  Required input is missing.
    Select in the contact widget  recipients  Draper
    Save the form
    The status message contains  Item created
    Location should be  ${PLONE_URL}/answer/view
    The page title is  test-out/10 - Answer
    The field links to  recipients  ${DIRECTORY_URL}/draper  John Draper
    Open the outgoing mail add form
    The internal reference number field shows  test-out/11

Edit an outgoing mail
    Create the mails folder
    Create an outgoing mail  answer  Answer
    Log in as site admin
    Open the outgoing mail edit form  ${MAILS_URL}/answer
    The internal reference number field shows  test-out/10
    Fill the title  Signed answer
    Fill the internal reference number  OUT-1
    Save the form
    The status message contains  Changes saved
    The page title is  OUT-1 - Signed answer
    The field shows  internal_reference_no  OUT-1

The internal reference number of an outgoing mail is unique
    Create the mails folder
    Create an outgoing mail  answer  Answer
    Create an outgoing mail  reminder  Reminder
    Log in as site admin
    Open the outgoing mail edit form  ${MAILS_URL}/reminder
    The internal reference number field shows  test-out/11
    Fill the internal reference number  test-out/10
    Save the form
    The field error contains  internal_reference_no  This value is already used. A good value would be: test-out/12
    # its own value is not a duplicate
    Fill the internal reference number  test-out/11
    Save the form
    The status message contains  Changes saved

An agent sees the internal reference number by default
    Create the mails folder
    Create an outgoing mail  answer  Answer
    Log in as agent
    Open the outgoing mail add form
    The internal reference number field shows  test-out/11
    Open the outgoing mail edit form  ${MAILS_URL}/answer
    The internal reference number field shows  test-out/10

The settings hide the internal reference number from an agent
    Create the mails folder
    Create an outgoing mail  answer  Answer
    Log in as site admin
    Change the outgoing mail settings  edit_irn=Always hide
    # an administrator still sees it
    Open the outgoing mail add form
    The internal reference number field shows  test-out/11
    Log in as agent
    Open the outgoing mail edit form  ${MAILS_URL}/answer
    The internal reference number field is hidden
    Open the outgoing mail add form
    The internal reference number field is hidden
    Fill the title  Reminder
    Select in the contact widget  recipients  Draper
    Save the form
    The status message contains  Item created
    # the internal reference number is given at creation
    The page title is  test-out/11 - Reminder
