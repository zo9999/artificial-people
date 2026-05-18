import logging

from flask import Blueprint, jsonify, request
import requests

from config import PUBLIC_WEBHOOK_BASE, AGENTPHONE_WEBHOOK_SECRET
from services.supabase_client import supabase
from services import agentmail, agentphone, sponge, face, memory, persona, voice_agent

log = logging.getLogger("people")

bp = Blueprint("people", __name__, url_prefix="/api/people")

PUBLIC_FIELDS = (
    "id, owner_id, first_name, last_name, address, email, phone, "
    "agentmail_inbox_id, agentphone_number_id, agentphone_agent_id, "
    "sponge_agent_id, sponge_wallet_address, face_url, face_prompt, "
    "credentials_text, created_at"
)


def _build_webhook_url(agent_id: str) -> str:
    if not PUBLIC_WEBHOOK_BASE:
        return ""
    base = f"{PUBLIC_WEBHOOK_BASE}/api/agentphone/webhook"
    parts = []
    if AGENTPHONE_WEBHOOK_SECRET:
        parts.append(f"secret={AGENTPHONE_WEBHOOK_SECRET}")
    parts.append(f"agentId={agent_id}")
    return base + "?" + "&".join(parts)


def _require_owner_id(value):
    if not value or not isinstance(value, str):
        return None, (jsonify({"error": "owner_id is required"}), 400)
    return value, None


def _person_owned(owner_id: str, person_id: str) -> bool:
    res = (
        supabase()
        .table("people")
        .select("id")
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    return bool(res.data)


def _service_error(service: str, exc: Exception):
    msg = str(exc)
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        msg = f"{exc.response.status_code}: {exc.response.text[:300]}"
    log.exception("service error [%s]: %s", service, msg)
    return jsonify({"service": service, "message": msg}), 502


@bp.get("")
def list_people():
    owner_id, err = _require_owner_id(request.args.get("owner_id"))
    if err:
        return err
    res = (
        supabase()
        .table("people")
        .select(PUBLIC_FIELDS)
        .eq("owner_id", owner_id)
        .order("created_at", desc=True)
        .execute()
    )
    return jsonify(res.data or [])


@bp.get("/<person_id>")
def get_person(person_id):
    owner_id, err = _require_owner_id(request.args.get("owner_id"))
    if err:
        return err
    res = (
        supabase()
        .table("people")
        .select(PUBLIC_FIELDS)
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return jsonify({"error": "not found"}), 404
    return jsonify(rows[0])


@bp.post("")
def create_person():
    body = request.get_json(silent=True) or {}
    owner_id, err = _require_owner_id(body.get("owner_id"))
    if err:
        return err

    required = ("first_name", "last_name", "address", "face_prompt")
    missing = [f for f in required if not (body.get(f) or "").strip()]
    if missing:
        return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400

    first_name = body["first_name"].strip()
    last_name = body["last_name"].strip()
    address = body["address"].strip()
    face_prompt = body["face_prompt"].strip()

    log.info("create_person owner=%s name=%s %s", owner_id, first_name, last_name)

    rollbacks: list[tuple[str, callable]] = []

    def _run_rollbacks():
        for service_name, fn in reversed(rollbacks):
            try:
                fn()
                log.info("rolled back %s", service_name)
            except Exception:
                log.exception("rollback failed for %s", service_name)

    def _fail(service_name: str, exc: Exception):
        _run_rollbacks()
        return _service_error(service_name, exc)

    try:
        log.info("→ face.generate_and_upload_face")
        face_url, full_prompt = face.generate_and_upload_face(face_prompt, owner_id)
        log.info("← face url=%s", face_url)
    except Exception as e:
        return _service_error("gemini", e)

    try:
        log.info("→ agentmail.create_inbox")
        inbox = agentmail.create_inbox(first_name, last_name)
        log.info("← agentmail inbox=%s email=%s", inbox.get("id"), inbox.get("email"))
        if inbox.get("id"):
            rollbacks.append(("agentmail", lambda: agentmail.delete_inbox(inbox["id"])))
    except Exception as e:
        return _fail("agentmail", e)

    voice_prompt = persona.build_voice_system_prompt(
        {
            "first_name": first_name,
            "last_name": last_name,
            "email": inbox["email"],
            "phone": "",
            "address": address,
        }
    )
    try:
        log.info("→ agentphone.create_agent (hosted voice)")
        ap_agent = agentphone.create_agent(
            f"{first_name} {last_name}", system_prompt=voice_prompt
        )
        log.info("← agentphone_agent id=%s", ap_agent.get("id"))
        if ap_agent.get("id"):
            rollbacks.append(("agentphone_agent", lambda: agentphone.delete_agent(ap_agent["id"])))
    except Exception as e:
        return _fail("agentphone", e)

    try:
        log.info("→ agentphone.provision_number")
        number = agentphone.provision_number()
        log.info("← agentphone id=%s phone=%s", number.get("id"), number.get("phone"))
        if number.get("id"):
            rollbacks.append(("agentphone_number", lambda: agentphone.release_number(number["id"])))
    except Exception as e:
        return _fail("agentphone", e)

    try:
        log.info("→ agentphone.attach_number agent=%s number=%s", ap_agent["id"], number["id"])
        agentphone.attach_number(ap_agent["id"], number["id"])
    except Exception as e:
        return _fail("agentphone", e)

    webhook_url = _build_webhook_url(ap_agent["id"])
    if webhook_url:
        try:
            log.info("→ agentphone.set_agent_webhook")
            agentphone.set_agent_webhook(ap_agent["id"], webhook_url, AGENTPHONE_WEBHOOK_SECRET)
        except Exception:
            log.exception("set_agent_webhook failed (continuing; can be repaired later)")
    else:
        log.warning("PUBLIC_WEBHOOK_BASE not set — skipping webhook configuration")

    try:
        log.info("→ sponge.create_agent")
        agent = sponge.create_agent(f"{first_name} {last_name}")
        log.info("← sponge agent=%s wallet=%s", agent.get("agent_id"), agent.get("wallet_address"))
        if agent.get("agent_id"):
            rollbacks.append(("sponge", lambda: sponge.delete_agent(agent["agent_id"])))
    except Exception as e:
        return _fail("sponge", e)

    log.info("inserting person row owner=%s", owner_id)

    row = {
        "owner_id": owner_id,
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "email": inbox["email"],
        "agentmail_inbox_id": inbox["id"],
        "phone": number["phone"],
        "agentphone_number_id": number["id"],
        "agentphone_agent_id": ap_agent["id"],
        "sponge_agent_id": agent["agent_id"],
        "sponge_wallet_address": agent["wallet_address"],
        "sponge_api_key": agent["scoped_api_key"],
        "face_url": face_url,
        "face_prompt": full_prompt,
    }
    try:
        res = supabase().table("people").insert(row).execute()
    except Exception as e:
        _run_rollbacks()
        log.exception("supabase insert failed")
        return jsonify({"service": "supabase", "message": str(e)}), 502

    inserted = (res.data or [None])[0]
    if inserted:
        inserted.pop("sponge_api_key", None)
    return jsonify(inserted), 201


@bp.patch("/<person_id>")
def update_person(person_id):
    body = request.get_json(silent=True) or {}
    owner_id, err = _require_owner_id(body.get("owner_id"))
    if err:
        return err

    editable = ("first_name", "last_name", "address", "face_prompt", "credentials_text")
    updates = {}
    for f in editable:
        v = body.get(f)
        if isinstance(v, str):
            updates[f] = v.strip() or None
    if not updates:
        return jsonify({"error": "no editable fields provided"}), 400

    sb = supabase()
    res = (
        sb.table("people")
        .update(updates)
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return jsonify({"error": "not found"}), 404
    updated = rows[0]
    updated.pop("sponge_api_key", None)
    try:
        voice_agent.refresh_by_id(owner_id, person_id)
    except Exception:
        log.exception("refresh voice agent after edit failed")
    return jsonify(updated)


@bp.get("/<person_id>/memories")
def list_memories(person_id):
    owner_id, err = _require_owner_id(request.args.get("owner_id"))
    if err:
        return err
    if not _person_owned(owner_id, person_id):
        return jsonify({"error": "not found"}), 404
    q = (request.args.get("q") or "").strip() or None
    try:
        items = memory.search_memories(person_id, q)
    except Exception as e:
        return _service_error("supermemory", e)
    return jsonify(items)


@bp.post("/<person_id>/memories")
def add_memory(person_id):
    body = request.get_json(silent=True) or {}
    owner_id, err = _require_owner_id(body.get("owner_id"))
    if err:
        return err
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content is required"}), 400
    if not _person_owned(owner_id, person_id):
        return jsonify({"error": "not found"}), 404
    try:
        added = memory.add_memory(person_id, owner_id, content)
    except Exception as e:
        return _service_error("supermemory", e)
    try:
        voice_agent.refresh_by_id(owner_id, person_id)
    except Exception:
        log.exception("refresh voice agent after memory failed")
    return jsonify(added), 201


@bp.post("/<person_id>/repair-agentphone")
def repair_agentphone(person_id):
    body = request.get_json(silent=True) or {}
    owner_id, err = _require_owner_id(body.get("owner_id"))
    if err:
        return err

    sb = supabase()
    res = (
        sb.table("people")
        .select("id, first_name, last_name, agentphone_number_id, agentphone_agent_id")
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return jsonify({"error": "not found"}), 404
    p = rows[0]
    if not p.get("agentphone_number_id"):
        return jsonify({"error": "missing agentphone_number_id"}), 400

    # Pull the full person so we can build a voice system prompt
    full = (
        sb.table("people")
        .select(PUBLIC_FIELDS)
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    full_row = (full.data or [{}])[0]
    voice_prompt = persona.build_voice_system_prompt(full_row)

    agent_id = p.get("agentphone_agent_id")
    created_new = False
    if not agent_id:
        try:
            ap_agent = agentphone.create_agent(
                f"{p['first_name']} {p['last_name']}", system_prompt=voice_prompt
            )
            agent_id = ap_agent["id"]
            created_new = True
        except Exception as e:
            return _service_error("agentphone", e)

        try:
            agentphone.attach_number(agent_id, p["agentphone_number_id"])
        except Exception as e:
            try:
                agentphone.delete_agent(agent_id)
            except Exception:
                log.exception("rollback delete_agent failed")
            return _service_error("agentphone", e)

        sb.table("people").update({"agentphone_agent_id": agent_id}).eq("id", person_id).execute()
    else:
        # Existing agent — push the latest voice prompt (with runs + memories) and hosted mode
        try:
            voice_agent.refresh(full_row)
        except Exception:
            log.exception("refresh voice agent failed (continuing)")

    webhook_url = _build_webhook_url(agent_id)
    webhook_set = False
    if webhook_url:
        try:
            agentphone.set_agent_webhook(agent_id, webhook_url, AGENTPHONE_WEBHOOK_SECRET)
            webhook_set = True
        except Exception:
            log.exception("set_agent_webhook failed during repair (continuing)")

    return jsonify(
        {
            "ok": True,
            "agent_id": agent_id,
            "created_new": created_new,
            "webhook_url": webhook_url or None,
            "webhook_set": webhook_set,
        }
    )


@bp.post("/<person_id>/regenerate-face")
def regenerate_face(person_id):
    body = request.get_json(silent=True) or {}
    owner_id, err = _require_owner_id(body.get("owner_id"))
    if err:
        return err

    sb = supabase()
    existing = (
        sb.table("people")
        .select("id, face_prompt")
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    rows = existing.data or []
    if not rows:
        return jsonify({"error": "not found"}), 404

    prompt = (body.get("face_prompt") or rows[0].get("face_prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "no face_prompt available"}), 400

    try:
        log.info("regenerate face person=%s", person_id)
        face_url, full_prompt = face.generate_and_upload_face(prompt, owner_id)
    except Exception as e:
        return _service_error("face", e)

    res = (
        sb.table("people")
        .update({"face_url": face_url, "face_prompt": full_prompt})
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .execute()
    )
    updated = (res.data or [None])[0]
    if updated:
        updated.pop("sponge_api_key", None)
    return jsonify(updated)
