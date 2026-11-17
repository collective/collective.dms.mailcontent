*** Settings ***
Documentation  The incoming mail: add form defaults (dates, internal reference number), required sender,
...            title "irn - title", next number, uniqueness of the internal reference number.
Resource  dms_mailcontent.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
Add an incoming mail
    Log in as site admin
    Open the incoming mail add form
    ${three_days_ago} =  Today  -3 days
    ${today} =  Today
    The date widget value is  original_mail_date  ${three_days_ago}
    The date widget value is  reception_date  ${today}
    The internal reference number field shows  test-in/10
    Fill the title  Invoice
    Select in the contact widget  sender  Rambo
    Save the form
    The status message contains  Item created
    Location should be  ${PLONE_URL}/invoice/view
    The page title is  test-in/10 - Invoice
    The field shows  internal_reference_no  test-in/10
    The field links to  sender  ${DIRECTORY_URL}/rambo  John Rambo
    The page is not an error

The next incoming mail proposes the next internal reference number
    Log in as site admin
    Open the incoming mail add form
    Fill the title  Invoice
    Select in the contact widget  sender  Rambo
    Save the form
    The status message contains  Item created
    Open the incoming mail add form
    The internal reference number field shows  test-in/11

The sender of an incoming mail is required
    Log in as site admin
    Open the incoming mail add form
    Fill the title  Invoice
    Save the form
    The status message contains  There were some errors
    The field error contains  sender  Required input is missing.

The internal reference number of an incoming mail is unique
    Create the mails folder
    Create an incoming mail  invoice  Invoice
    Log in as site admin
    Open the incoming mail add form
    Fill the title  Second invoice
    Select in the contact widget  sender  Rambo
    Fill the internal reference number  test-in/10
    Save the form
    The field error contains  internal_reference_no  This value is already used. A good value would be: test-in/11
    Fill the internal reference number  test-in/11
    Save the form
    The status message contains  Item created
    The page title is  test-in/11 - Second invoice

An incoming mail cannot reply to itself
    Create the mails folder
    Create an incoming mail  invoice  Invoice
    Log in as site admin
    Go to  ${MAILS_URL}/invoice
    Click the content view  edit
    Select in the related items widget  reply_to  Invoice
    The related items widget contains  reply_to  test-in/10 - Invoice
    Save the form
    The field error contains  reply_to  You cannot choose the current object as a reply to.
