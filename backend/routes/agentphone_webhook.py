import logging

from flask import Blueprint, jsonify, request

from config import AGENTPHONE_WEBHOOK_SECRET
from services.supabase_client import supabase
from services.runner import start_run
from services import intent

log = logging.getLogger("webhook")
bp = Blueprint("agentphone_webhook", __name__, url_prefix="/api/agentphone")


def _check_secret() -> bool:
    if not AGENTPHONE_WEBHOOK_SECRET:
        return True
    provided = (
        request.headers.get("X-Webhook-Secret")
        or request.args.get("secret")
        or ""
    )
    return provided == AGENTPHONE_WEBHOOK_SECRET


def _pluck(data: dict, *keys):
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return None


@bp.post("/webhook")
def inbound():
    if not _check_secret():
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    log.info("inbound webhook payload=%r", payload)

    body_root = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    event = payload.get("event") or payload.get("type") or body_root.get("event") or ""

    agent_id = (
        request.args.get("agentId")
        or _pluck(payload, "agentId", "agent_id")
        or _pluck(body_root, "agentId", "agent_id")
    )
    to_number = _pluck(body_root, "to", "toNumber", "to_number", "recipient")
    from_number = _pluck(body_root, "from", "fromNumber", "from_number", "sender")
    text = _pluck(body_root, "text", "body", "content", "message")

    if not text:
        log.warning("webhook missing text; ignoring")
        return jsonify({"ok": True, "ignored": True}), 200

    if "outbound" in str(event).lower() or _pluck(body_root, "direction") == "outbound":
        return jsonify({"ok": True, "skipped_outbound": True}), 200

    sb = supabase()
    person = None
    if agent_id:
        res = (
            sb.table("people")
            .select("*")
            .eq("agentphone_agent_id", agent_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if rows:
            person = rows[0]
    if person is None and to_number:
        res = (
            sb.table("people")
            .select("*")
            .eq("phone", to_number)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if rows:
            person = rows[0]
    if person is None:
        log.warning("no AP matches agent_id=%s to=%s", agent_id, to_number)
        return jsonify({"ok": True, "unknown": True}), 200

    if not intent.is_actionable(text):
        log.info("sms classified IGNORE: %r", text[:120])
        return jsonify({"ok": True, "ignored": True, "reason": "not actionable"}), 200

    run = start_run(person, text, reply_to=from_number)
    return jsonify({"ok": True, "run": run}), 202
