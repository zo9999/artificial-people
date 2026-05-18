import logging

from agentmail import AgentMail

from config import AGENTMAIL_API_KEY, AGENTMAIL_DOMAIN

log = logging.getLogger("agentmail")
_client = AgentMail(api_key=AGENTMAIL_API_KEY)


def _resolve_create_request_cls():
    """Locate the CreateInboxRequest class across known SDK layouts."""
    candidates = (
        "agentmail.CreateInboxRequest",
        "agentmail.types.CreateInboxRequest",
        "agentmail.types.create_inbox_request.CreateInboxRequest",
        "agentmail.inboxes.types.CreateInboxRequest",
        "agentmail.inboxes.types.create_inbox_request.CreateInboxRequest",
    )
    import importlib
    for path in candidates:
        module_path, cls_name = path.rsplit(".", 1)
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, cls_name, None)
            if cls is not None:
                return cls
        except Exception:
            continue
    return None


def create_inbox(first_name: str, last_name: str) -> dict:
    username = f"{first_name}.{last_name}".lower().replace(" ", "")
    display_name = f"{first_name} {last_name}"
    log.info("create_inbox username=%s domain=%s", username, AGENTMAIL_DOMAIN)

    payload = {
        "username": username,
        "domain": AGENTMAIL_DOMAIN,
        "display_name": display_name,
    }

    inbox = None
    last_err: Exception | None = None

    # Try 1: typed request object if we can find it
    RequestCls = _resolve_create_request_cls()
    if RequestCls is not None:
        try:
            inbox = _client.inboxes.create(request=RequestCls(**payload))
        except Exception as e:
            last_err = e
            log.warning("create(request=RequestCls) failed: %s", e)

    # Try 2: pass plain dict as request
    if inbox is None:
        try:
            inbox = _client.inboxes.create(request=payload)
        except Exception as e:
            last_err = e
            log.warning("create(request=dict) failed: %s", e)

    # Try 3: bare kwargs (oldest SDK shape)
    if inbox is None:
        try:
            inbox = _client.inboxes.create(**payload)
        except Exception as e:
            last_err = e
            log.warning("create(**kwargs) failed: %s", e)

    # Try 4: positional dict
    if inbox is None:
        try:
            inbox = _client.inboxes.create(payload)
        except Exception as e:
            last_err = e
            log.warning("create(payload) failed: %s", e)

    # Try 5: zero-arg fallback (auto-generated address)
    if inbox is None:
        log.warning("all create() shapes failed; falling back to no-arg create")
        try:
            inbox = _client.inboxes.create()
        except Exception:
            log.exception("agentmail create_inbox totally failed")
            if last_err:
                raise last_err
            raise

    return {
        "id": (
            getattr(inbox, "inbox_id", None)
            or getattr(inbox, "id", None)
        ),
        "email": (
            getattr(inbox, "email", None)
            or getattr(inbox, "address", None)
            or getattr(inbox, "inbox_id", None)
        ),
    }


def delete_inbox(inbox_id: str) -> None:
    log.info("delete_inbox %s", inbox_id)
    _client.inboxes.delete(inbox_id=inbox_id)
