import logging

from flask import Blueprint, jsonify, request

import threading

from config import AGENTPHONE_WEBHOOK_SECRET
from services.supabase_client import supabase
from services.runner import start_run
from services import intent, voice_chat

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
    raw_text = _pluck(body_root, "text", "body", "content", "message", "transcript", "utterance")
    if isinstance(raw_text, list):
        # AgentPhone occasionally sends transcript as [{role,content}, ...] or [str, ...]
        parts = []
        for item in raw_text:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(
                    str(item.get("content") or item.get("text") or item.get("transcript") or "")
                )
        text = " ".join(p for p in parts if p).strip()
    else:
        text = str(raw_text) if raw_text is not None else ""

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

    channel = (payload.get("channel") or body_root.get("channel") or "").lower()

    # ----- VOICE during call: reply synchronously, fire run in background -----
    if channel == "voice":
        recent = (
            body_root.get("recentMessages")
            or body_root.get("history")
            or body_root.get("transcript")
            or []
        )
        if isinstance(recent, dict):
            recent = []
        actionable = intent.is_actionable(text)
        if actionable:
            log.info("voice utterance ACT: %r", text[:120])
            threading.Thread(
                target=start_run, args=(person, text, from_number), daemon=True
            ).start()
            return jsonify({"text": voice_chat.ack_action(text)}), 200
        reply = voice_chat.reply(person, recent, text)
        log.info("voice utterance reply: %r", reply[:120])
        return jsonify({"text": reply}), 200

    # ----- SMS: classify, ack via outbound SMS handled by runner -----
    if not intent.is_actionable(text):
        log.info("sms classified IGNORE: %r", text[:120])
        return jsonify({"ok": True, "ignored": True, "reason": "not actionable"}), 200

    run = start_run(person, text, reply_to=from_number)
    return jsonify({"ok": True, "run": run}), 202
