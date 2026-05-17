import logging

from agentmail import AgentMail

from config import AGENTMAIL_API_KEY, AGENTMAIL_DOMAIN

log = logging.getLogger("agentmail")
_client = AgentMail(api_key=AGENTMAIL_API_KEY)


def create_inbox(first_name: str, last_name: str) -> dict:
    username = f"{first_name}.{last_name}".lower().replace(" ", "")
    display_name = f"{first_name} {last_name}"
    log.info("create_inbox username=%s domain=%s", username, AGENTMAIL_DOMAIN)
    inbox = _client.inboxes.create(
        username=username,
        domain=AGENTMAIL_DOMAIN,
        display_name=display_name,
    )
    return {
        "id": getattr(inbox, "inbox_id", None) or getattr(inbox, "id", None),
        "email": getattr(inbox, "email", None) or getattr(inbox, "address", None),
    }


def delete_inbox(inbox_id: str) -> None:
    log.info("delete_inbox %s", inbox_id)
    _client.inboxes.delete(inbox_id=inbox_id)
