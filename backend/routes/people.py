from flask import Blueprint, jsonify, request
import requests

from services.supabase_client import supabase
from services import agentmail, agentphone, sponge, face

bp = Blueprint("people", __name__, url_prefix="/api/people")

PUBLIC_FIELDS = (
    "id, owner_id, first_name, last_name, address, email, phone, "
    "agentmail_inbox_id, agentphone_number_id, sponge_agent_id, "
    "sponge_wallet_address, face_url, face_prompt, created_at"
)


def _require_owner_id(value):
    if not value or not isinstance(value, str):
        return None, (jsonify({"error": "owner_id is required"}), 400)
    return value, None


def _service_error(service: str, exc: Exception):
    msg = str(exc)
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        msg = f"{exc.response.status_code}: {exc.response.text[:300]}"
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

    try:
        face_url, full_prompt = face.generate_and_upload_face(face_prompt, owner_id)
    except Exception as e:
        return _service_error("gemini", e)

    try:
        inbox = agentmail.create_inbox(first_name, last_name)
    except Exception as e:
        return _service_error("agentmail", e)

    try:
        number = agentphone.provision_number()
    except Exception as e:
        return _service_error("agentphone", e)

    try:
        agent = sponge.create_agent(f"{first_name} {last_name}")
    except Exception as e:
        return _service_error("sponge", e)

    row = {
        "owner_id": owner_id,
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "email": inbox["email"],
        "agentmail_inbox_id": inbox["id"],
        "phone": number["phone"],
        "agentphone_number_id": number["id"],
        "sponge_agent_id": agent["agent_id"],
        "sponge_wallet_address": agent["wallet_address"],
        "sponge_api_key": agent["scoped_api_key"],
        "face_url": face_url,
        "face_prompt": full_prompt,
    }
    res = supabase().table("people").insert(row).execute()
    inserted = (res.data or [None])[0]
    if inserted:
        inserted.pop("sponge_api_key", None)
    return jsonify(inserted), 201
