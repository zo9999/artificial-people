import requests

from config import AGENTPHONE_API_KEY, AGENTPHONE_BASE_URL

_HEADERS = {
    "Authorization": f"Bearer {AGENTPHONE_API_KEY}",
    "Content-Type": "application/json",
}


def provision_number() -> dict:
    r = requests.post(
        f"{AGENTPHONE_BASE_URL}/v1/numbers",
        headers=_HEADERS,
        json={"country": "US"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return {
        "id": data.get("id") or data.get("number_id"),
        "phone": data.get("phone_number") or data.get("number") or data.get("e164"),
    }
