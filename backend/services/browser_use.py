import logging

import requests

from config import BROWSER_USE_API_KEY, BROWSER_USE_BASE_URL

log = logging.getLogger("browser_use")

_HEADERS = {
    "X-Browser-Use-API-Key": BROWSER_USE_API_KEY,
    "Content-Type": "application/json",
}


def create_task(prompt: str) -> dict:
    url = f"{BROWSER_USE_BASE_URL}/tasks"
    log.info("POST %s key_set=%s prompt_len=%d", url, bool(BROWSER_USE_API_KEY), len(prompt))
    r = requests.post(url, headers=_HEADERS, json={"task": prompt}, timeout=30)
    log.info("← %s %s", r.status_code, r.text[:300])
    r.raise_for_status()
    data = r.json()
    return {
        "task_id": data.get("id") or data.get("taskId"),
        "session_id": data.get("sessionId") or data.get("session_id"),
    }


def get_session(session_id: str) -> dict:
    url = f"{BROWSER_USE_BASE_URL}/sessions/{session_id}"
    log.info("GET %s", url)
    r = requests.get(url, headers=_HEADERS, timeout=30)
    log.info("← %s", r.status_code)
    r.raise_for_status()
    data = r.json()
    return {
        "live_url": data.get("liveUrl") or data.get("live_url"),
        "status": (data.get("status") or "").lower(),
        "raw": data,
    }


def get_task(task_id: str) -> dict:
    url = f"{BROWSER_USE_BASE_URL}/tasks/{task_id}"
    log.info("GET %s", url)
    r = requests.get(url, headers=_HEADERS, timeout=30)
    log.info("← %s", r.status_code)
    r.raise_for_status()
    data = r.json()
    return {
        "status": (data.get("status") or "").lower(),
        "result": data.get("result") or data.get("output") or "",
        "raw": data,
    }


def stop_session(session_id: str) -> None:
    url = f"{BROWSER_USE_BASE_URL}/sessions/{session_id}"
    log.info("PATCH %s action=stop", url)
    try:
        requests.patch(url, headers=_HEADERS, json={"action": "stop"}, timeout=30)
    except Exception as e:
        log.warning("stop_session failed: %s", e)
