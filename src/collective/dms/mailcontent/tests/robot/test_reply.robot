*** Settings ***
Documentation  Reply to an incoming mail (@@reply): prefilled outgoing mail created next to the incoming mail,
...            links between both mails, treating groups of the incoming mail added to the recipient groups,
...            internal reference number shown only when replying (settings).
Resource  dms_mailcontent.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Keywords ***
Reply to the invoice
    [Documentation]  Incoming mail /mails/invoice (test-in/10) sent by Rambo, treated by Reviewers
    Create the mails folder
    Create an incoming mail  invoice  Invoice
    Log in as site admin
    Go to  ${MAILS_URL}/invoice/@@reply


*** Test Cases ***
The reply form is prefilled with the incoming mail
    Reply to the invoice
    The page title contains  Reply to test-in/10 - Invoice
    The text field shows  IDublinCore-title  Invoice
    The contact is selected in the widget  recipients  ${DIRECTORY_URL}/rambo
    The related items widget contains  reply_to  test-in/10 - Invoice
    The text field shows  external_reference_no  EXT-invoice
    The internal reference number field shows  test-out/10

Reply to an incoming mail
    Reply to the invoice
    Save the form
    The status message contains  Item created
    # created in the folder of the incoming mail
    Location should be  ${MAILS_URL}/invoice-1/view
    The page title is  test-out/10 - Invoice
    The field links to  recipients  ${DIRECTORY_URL}/rambo  John Rambo
    The field links to  reply_to  ${MAILS_URL}/invoice  test-in/10 - Invoice

The reply form is prefilled with the treating groups of the incoming mail
    [Documentation]  Plone 4 bug: ReplyForm.updateWidgets sets the widget value after the update of the
    ...              ordered selection widget, which computed its selected items: no treating group shown nor saved
    [Tags]  plone4-bug
    Reply to the invoice
    The multiple selection widget contains  treating_groups  Reviewers
    Save the form
    The status message contains  Item created
    The field shows  treating_groups  Reviewers

The incoming mail view shows its replies
    [Documentation]  Back references of the reply_to field
    Reply to the invoice
    Save the form
    The status message contains  Item created
    Go to  ${MAILS_URL}/invoice
    The field links to  reply_to  ${MAILS_URL}/invoice-1  test-out/10 - Invoice

The reply adds the treating groups of the incoming mail to the recipient groups
    Reply to the invoice
    Replace the selection of the multiple selection widget  treating_groups  Administrators
    Save the form
    The status message contains  Item created
    The field shows  treating_groups  Administrators
    The field shows  recipient_groups  Reviewers

The internal reference number is shown to an agent only when replying
    Create the mails folder
    Create an incoming mail  invoice  Invoice
    Create an outgoing mail  answer  Answer
    Log in as site admin
    Change the outgoing mail settings  edit_irn=Show only when replying
    Log in as agent
    Open the outgoing mail add form
    The internal reference number field is hidden
    Open the outgoing mail edit form  ${MAILS_URL}/answer
    The internal reference number field is hidden
    Go to  ${MAILS_URL}/invoice/@@reply
    The internal reference number field shows  test-out/11
    Save the form
    The status message contains  Item created
    Open the outgoing mail edit form  ${MAILS_URL}/invoice-1
    The internal reference number field shows  test-out/11
