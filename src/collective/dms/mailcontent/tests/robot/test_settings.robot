*** Settings ***
Documentation  The Dms Mail settings control panel: number and expression of the next internal reference
...            numbers, increment and mail date options of the outgoing mails.
Resource  dms_mailcontent.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
Change the incoming mail internal reference number
    Log in as site admin
    Open the settings
    The text field shows  incomingmail_number  10
    The text field shows  incomingmail_talexpression  python:'test-in/'+number
    Fill the text field  incomingmail_number  50
    Fill the text field  incomingmail_talexpression  python:'IN-%s-%s' % (date.year(), number)
    Save the form
    The status message contains  Changes saved
    Open the incoming mail add form
    ${year} =  Get current date  result_format=%Y
    The internal reference number field shows  IN-${year}-50

Change the outgoing mail internal reference number
    Log in as site admin
    Open the settings
    Click the form tab  Outgoing mail
    Fill the text field  outgoingmail_number  7
    Fill the text field  outgoingmail_talexpression  python:'OUT/' + number
    Save the form
    The status message contains  Changes saved
    Open the outgoing mail add form
    The internal reference number field shows  OUT/7

An invalid expression shows the error as internal reference number
    Log in as site admin
    Open the settings
    Fill the text field  incomingmail_talexpression  python:unknown
    Save the form
    The status message contains  Changes saved
    Open the incoming mail add form
    The internal reference number field starts with  Error in expression:

The outgoing mail number is not incremented when the setting is off
    [Documentation]  Only when the user can edit the internal reference number
    Log in as site admin
    Change the outgoing mail settings  increment=${False}
    Open the outgoing mail add form
    Fill the title  Answer
    Select in the contact widget  recipients  Draper
    Fill the internal reference number  OUT-MANUAL
    Save the form
    The status message contains  Item created
    The page title is  OUT-MANUAL - Answer
    Open the outgoing mail add form
    The internal reference number field shows  test-out/10

The mail date of a new outgoing mail is empty when the setting is off
    Log in as site admin
    Change the outgoing mail settings  today=${False}
    Open the outgoing mail add form
    The date widget is empty  mail_date
