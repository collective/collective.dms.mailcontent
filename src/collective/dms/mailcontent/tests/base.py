"""Helpers shared by the test modules."""

from plone import api
from z3c.relationfield.relation import RelationValue
from zope.component import getUtility
from zope.i18n import translate
from zope.intid.interfaces import IIntIds

PREFIX = "collective.dms.mailcontent.browser.settings.IDmsMailConfig."
IM_NUMBER = PREFIX + "incomingmail_number"
IM_EXPRESSION = PREFIX + "incomingmail_talexpression"
OM_NUMBER = PREFIX + "outgoingmail_number"
OM_EXPRESSION = PREFIX + "outgoingmail_talexpression"
OM_EDIT_IRN = PREFIX + "outgoingmail_edit_irn"
OM_INCREMENT = PREFIX + "outgoingmail_increment_number"
OM_TODAY = PREFIX + "outgoingmail_today_mail_date"


def rel(obj):
    """A relation value to obj, as the edit forms store it."""
    return RelationValue(getUtility(IIntIds).getId(obj))


def create_contacts(portal):
    """A directory with an organization, sender of the incoming mails."""
    config = [{"name": "ud", "token": "ud"}]
    directory = api.content.create(
        container=portal,
        type="directory",
        id="dir",
        title="Directory",
        organization_types=config,
        organization_levels=config,
        position_types=config,
    )
    return api.content.create(
        container=directory, type="organization", id="imio", title="IMIO"
    )


def set_form(request, data=None, method="GET"):
    """Replace the submitted values: request.form and their copy in request.other (z3c.form reads both)."""
    for key in list(request.other.keys()):
        if key.startswith("form.") or key in request.form:
            del request.other[key]
    request.form.clear()
    request.form.update(data or {})
    request["REQUEST_METHOD"] = method


def clean_request(request):
    """Remove the keys the outgoing mail forms put in the request."""
    for key in ("_hide_irn", "_auto_ref", "_irn"):
        request.other.pop(key, None)


def form_errors(form):
    """The translated error messages of the form widgets, by widget name."""
    return {
        name: translate(widget.error.message, context=form.request)
        for name, widget in form.widgets.items()
        if widget.error
    }
