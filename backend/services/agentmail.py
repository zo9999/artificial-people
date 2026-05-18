import logging

from agentmail import AgentMail
from agentmail.inboxes.types.create_inbox_request import CreateInboxRequest

from config import AGENTMAIL_API_KEY, AGENTMAIL_DOMAIN

log = logging.getLogger("agentmail")
_client = AgentMail(api_key=AGENTMAIL_API_KEY)


def create_inbox(first_name: str, last_name: str) -> dict:
    username = f"{first_name}.{last_name}".lower().replace(" ", "")
    display_name = f"{first_name} {last_name}"
    log.info("create_inbox username=%s domain=%s", username, AGENTMAIL_DOMAIN)

    inbox = _client.inboxes.create(
        request=CreateInboxRequest(
            username=username,
            domain=AGENTMAIL_DOMAIN,
            display_name=display_name,
        )
    )

    # The Inbox model exposes inbox_id (which IS the full email like jane@agentmail.to)
    inbox_id = getattr(inbox, "inbox_id", None) or getattr(inbox, "id", None)
    return {
        "id": inbox_id,
        "email": (
            getattr(inbox, "email", None)
            or getattr(inbox, "address", None)
            or inbox_id
        ),
    }


def delete_inbox(inbox_id: str) -> None:
    log.info("delete_inbox %s", inbox_id)
    _client.inboxes.delete(inbox_id=inbox_id)
