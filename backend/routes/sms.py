import logging

from flask import Blueprint, jsonify, request

from services.supabase_client import supabase
from services import agentphone

log = logging.getLogger("sms")
bp = Blueprint("sms", __name__)


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
