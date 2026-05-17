import logging

import requests

from config import SPONGE_MASTER_KEY, SPONGE_BASE_URL

log = logging.getLogger("sponge")

_MASTER_HEADERS = {
    "Authorization": f"Bearer {SPONGE_MASTER_KEY}",
    "Content-Type": "application/json",
}


def _agent_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _get_wallet_addresses(agent_api_key: str) -> dict:
    url = f"{SPONGE_BASE_URL}/api/wallets/"
    log.info("GET %s", url)
    r = requests.get(url, headers=_agent_headers(agent_api_key), timeout=30)
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    data = r.json()
    wallets = data.get("wallets") if isinstance(data, dict) else data
    if not isinstance(wallets, list):
        return {}
    by_chain = {}
    for w in wallets:
        chain = (w.get("chain") or w.get("network") or "").lower()
        addr = w.get("address")
        if chain and addr:
            by_chain[chain] = addr
    return by_chain


def delete_agent(agent_id: str) -> None:
    url = f"{SPONGE_BASE_URL}/api/agents/{agent_id}"
    log.info("DELETE %s", url)
    r = requests.delete(url, headers=_MASTER_HEADERS, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:200])
    r.raise_for_status()


def issue_virtual_card(agent_api_key: str, merchant: str, amount_cents: int) -> dict:
    url = f"{SPONGE_BASE_URL}/api/cards/issue-virtual-card"
    log.info("POST %s merchant=%s cap_cents=%d", url, merchant, amount_cents)
    r = requests.post(
        url,
        headers=_agent_headers(agent_api_key),
        json={
            "merchant": merchant,
            "amountCents": amount_cents,
            "amount": amount_cents / 100.0,
        },
        timeout=60,
    )
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    data = r.json()
    card = data.get("card") if isinstance(data, dict) else None
    src = card if isinstance(card, dict) else data
    number = src.get("number") or src.get("pan") or src.get("cardNumber")
    return {
        "id": src.get("id") or src.get("card_id") or src.get("cardId"),
        "number": number,
        "last4": src.get("last4") or (number[-4:] if number else None),
        "exp": src.get("exp") or src.get("expiration") or src.get("expiry"),
        "cvc": src.get("cvc") or src.get("cvv"),
    }


def create_agent(name: str) -> dict:
    url = f"{SPONGE_BASE_URL}/api/agents/"
    log.info("POST %s key_set=%s", url, bool(SPONGE_MASTER_KEY))
    r = requests.post(url, headers=_MASTER_HEADERS, json={"name": name}, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    data = r.json()

    agent = data.get("agent") or {}
    agent_id = agent.get("id") or data.get("id") or data.get("agent_id")
    scoped_key = data.get("apiKey") or data.get("api_key") or data.get("scoped_api_key")

    wallet_address = None
    if scoped_key:
        try:
            addrs = _get_wallet_addresses(scoped_key)
            wallet_address = addrs.get("base") or addrs.get("ethereum") or addrs.get("solana")
        except Exception as e:
            log.warning("failed to fetch wallet addresses: %s", e)

    return {
        "agent_id": agent_id,
        "scoped_api_key": scoped_key,
        "wallet_address": wallet_address,
    }
