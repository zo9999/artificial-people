import logging
import re

from flask import Blueprint, Response, jsonify, request

from services.supabase_client import supabase
from services import agentphone

log = logging.getLogger("sms")
bp = Blueprint("sms", __name__)

_CODE_RE = re.compile(r"\b\d{4,8}\b")


def _require_owner_id(value):
    if not value or not isinstance(value, str):
        return None, (jsonify({"error": "owner_id is required"}), 400)
    return value, None


@bp.get("/api/people/<person_id>/messages")
def list_messages(person_id):
    owner_id, err = _require_owner_id(request.args.get("owner_id"))
    if err:
        return err
    res = (
        supabase()
        .table("people")
        .select("phone, agentphone_number_id")
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return jsonify({"error": "not found"}), 404
    number_id = rows[0].get("agentphone_number_id")
    phone = rows[0].get("phone") or ""
    if not number_id:
        return jsonify([])
    try:
        msgs = agentphone.list_messages_for_number_id(number_id, phone)
    except Exception as e:
        log.exception("list_messages failed")
        return jsonify({"service": "agentphone", "message": str(e)}), 502
    return jsonify(msgs)


@bp.get("/api/inbox/<person_id>/latest")
def latest_inbox(person_id):
    """Public, no-auth endpoint the browser agent fetches to read 2FA codes."""
    res = (
        supabase()
        .table("people")
        .select("phone, agentphone_number_id")
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return Response("not found", status=404, mimetype="text/plain")
    number_id = rows[0].get("agentphone_number_id")
    phone = rows[0].get("phone") or ""
    if not number_id:
        return Response("no inbox", status=200, mimetype="text/plain")
    try:
        msgs = agentphone.list_messages_for_number_id(number_id, phone, limit=10)
    except Exception as e:
        log.exception("latest_inbox failed")
        return Response(f"error: {e}", status=502, mimetype="text/plain")

    inbound = [m for m in msgs if m.get("direction") == "in"]
    inbound.sort(key=lambda m: m.get("created_at") or "", reverse=True)
    inbound = inbound[:5]

    lines = [f"Inbox for {phone}", "=" * 40, ""]
    if not inbound:
        lines.append("(no inbound messages)")
    for m in inbound:
        ts = m.get("created_at") or ""
        sender = m.get("from") or "?"
        body = m.get("body") or ""
        codes = _CODE_RE.findall(body)
        lines.append(f"FROM {sender}  AT {ts}")
        if codes:
            lines.append("LIKELY CODE(S): " + ", ".join(codes))
        lines.append(body)
        lines.append("-" * 40)
    return Response("\n".join(lines), status=200, mimetype="text/plain")
