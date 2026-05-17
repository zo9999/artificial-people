from agentmail import AgentMail

from config import AGENTMAIL_API_KEY, AGENTMAIL_DOMAIN

_client = AgentMail(api_key=AGENTMAIL_API_KEY)


def create_inbox(first_name: str, last_name: str) -> dict:
    username = f"{first_name}.{last_name}".lower().replace(" ", "")
    display_name = f"{first_name} {last_name}"
    inbox = _client.inboxes.create(
        username=username,
        domain=AGENTMAIL_DOMAIN,
        display_name=display_name,
    )
    return {
        "id": getattr(inbox, "inbox_id", None) or getattr(inbox, "id", None),
        "email": getattr(inbox, "email", None) or getattr(inbox, "address", None),
    }
