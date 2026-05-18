import logging

import requests

from config import AGENTPHONE_API_KEY, AGENTPHONE_BASE_URL

log = logging.getLogger("agentphone")

_HEADERS = {
    "Authorization": f"Bearer {AGENTPHONE_API_KEY}",
    "Content-Type": "application/json",
}


def create_agent(name: str, system_prompt: str = "") -> dict:
    url = f"{AGENTPHONE_BASE_URL}/v1/agents"
    payload = {
        "name": name,
        "voiceMode": "hosted",
        "messagingTools": True,
    }
    if system_prompt:
        payload["systemPrompt"] = system_prompt
    log.info("POST %s name=%s voiceMode=hosted", url, name)
    r = requests.post(url, headers=_HEADERS, json=payload, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    data = r.json()
    return {"id": data.get("id") or data.get("agent_id") or data.get("agentId")}


def update_agent(agent_id: str, **fields) -> None:
    url = f"{AGENTPHONE_BASE_URL}/v1/agents/{agent_id}"
    log.info("PATCH %s fields=%s", url, list(fields.keys()))
    r = requests.patch(url, headers=_HEADERS, json=fields, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:200])
    r.raise_for_status()


def delete_agent(agent_id: str) -> None:
    url = f"{AGENTPHONE_BASE_URL}/v1/agents/{agent_id}"
    log.info("DELETE %s", url)
    r = requests.delete(url, headers=_HEADERS, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:200])
    r.raise_for_status()


def attach_number(agent_id: str, number_id: str) -> None:
    url = f"{AGENTPHONE_BASE_URL}/v1/agents/{agent_id}/numbers"
    log.info("POST %s number_id=%s", url, number_id)
    r = requests.post(
        url,
        headers=_HEADERS,
        json={"numberId": number_id, "number_id": number_id},
        timeout=30,
    )
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()


def set_agent_webhook(agent_id: str, url_value: str, secret: str = "") -> None:
    url = f"{AGENTPHONE_BASE_URL}/v1/agents/{agent_id}/webhook"
    payload = {
        "url": url_value,
        "events": ["message.received"],
    }
    if secret:
        payload["secret"] = secret
    log.info("POST %s webhook_url=%s", url, url_value)
    r = requests.post(url, headers=_HEADERS, json=payload, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()


def provision_number() -> dict:
    url = f"{AGENTPHONE_BASE_URL}/v1/numbers"
    log.info("POST %s key_set=%s", url, bool(AGENTPHONE_API_KEY))
    r = requests.post(url, headers=_HEADERS, json={"country": "US"}, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    data = r.json()
    return {
        "id": data.get("id") or data.get("number_id"),
        "phone": (
            data.get("phoneNumber")
            or data.get("phone_number")
            or data.get("number")
            or data.get("e164")
        ),
    }


def release_number(number_id: str) -> None:
    url = f"{AGENTPHONE_BASE_URL}/v1/numbers/{number_id}"
    log.info("DELETE %s", url)
    r = requests.delete(url, headers=_HEADERS, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:200])
    r.raise_for_status()


def send_message(from_number: str, to_number: str, body: str) -> dict:
    url = f"{AGENTPHONE_BASE_URL}/v1/messages"
    payload = {"from": from_number, "to": to_number, "text": body, "body": body}
    log.info("POST %s from=%s to=%s len=%d", url, from_number, to_number, len(body))
    r = requests.post(url, headers=_HEADERS, json=payload, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:200])
    r.raise_for_status()
    return r.json() if r.text else {}


def _first(d: dict, *keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return None


def list_messages_for_number_id(number_id: str, ap_phone: str, limit: int = 100) -> list[dict]:
    """Fetch SMS for the AgentPhone number identified by `number_id`."""
    url = f"{AGENTPHONE_BASE_URL}/v1/numbers/{number_id}/messages"
    log.info("GET %s", url)
    r = requests.get(url, headers=_HEADERS, params={"limit": limit}, timeout=30)
    log.info("← %s", r.status_code)
    r.raise_for_status()
    data = r.json()
    items = data if isinstance(data, list) else (
        data.get("messages") or data.get("data") or data.get("results") or []
    )
    if items:
        log.info("sample message keys=%s", sorted(list(items[0].keys()))[:30])
    out = []
    for m in items:
        to_n = _first(m, "to", "toNumber", "to_number", "toE164", "to_e164", "recipient")
        from_n = _first(
            m, "from", "fromNumber", "from_number", "fromE164", "from_e164",
            "sender", "senderNumber", "sender_number", "author",
        )
        direction = (m.get("direction") or m.get("type") or "").lower()
        if direction.startswith("in") or direction == "received":
            direction = "in"
        elif direction.startswith("out") or direction == "sent":
            direction = "out"
        else:
            direction = "in" if to_n == ap_phone else "out"
        out.append(
            {
                "id": _first(m, "id", "messageId", "message_id"),
                "from": from_n,
                "to": to_n,
                "body": _first(m, "text", "body", "content", "message") or "",
                "direction": direction,
                "created_at": _first(
                    m, "createdAt", "created_at", "timestamp",
                    "sentAt", "sent_at", "receivedAt", "received_at", "time",
                ),
            }
        )
    out.sort(key=lambda x: x.get("created_at") or "")
    return out
