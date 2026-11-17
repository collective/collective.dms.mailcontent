*** Settings ***
Documentation  The sending type behavior (radio, "Normal" by default), on the testtype of the testing profile.
Resource  dms_mailcontent.robot
Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***
Choose the sending type
    Log in as site admin
    Go to  ${PLONE_URL}
    Click the add menu item  testtype
    The radio field is set to  ISendingType.sending_type  normal
    Select in the radio field  ISendingType.sending_type  registered
    Save the form
    The status message contains  Item created
    The field shows  ISendingType-sending_type  Registered
