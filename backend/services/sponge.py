import requests

from config import SPONGE_MASTER_KEY, SPONGE_BASE_URL

_HEADERS = {
    "Authorization": f"Bearer {SPONGE_MASTER_KEY}",
    "Content-Type": "application/json",
}


def create_agent(name: str) -> dict:
    r = requests.post(
        f"{SPONGE_BASE_URL}/v1/agents",
        headers=_HEADERS,
        json={"name": name},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return {
        "agent_id": data.get("id") or data.get("agent_id"),
        "scoped_api_key": data.get("api_key") or data.get("scoped_api_key"),
        "wallet_address": (
            data.get("wallet_address")
            or (data.get("wallet") or {}).get("address")
            or (data.get("evm") or {}).get("address")
        ),
    }
