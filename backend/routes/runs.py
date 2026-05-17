from flask import Blueprint, jsonify, request

from services.supabase_client import supabase

bp = Blueprint("runs", __name__)

RUN_FIELDS = "id, owner_id, person_id, trigger_text, bu_session_id, bu_live_url, status, result, created_at"


def _require_owner_id(value):
    if not value or not isinstance(value, str):
        return None, (jsonify({"error": "owner_id is required"}), 400)
    return value, None


@bp.get("/api/people/<person_id>/runs")
def list_runs(person_id):
    owner_id, err = _require_owner_id(request.args.get("owner_id"))
    if err:
        return err
    res = (
        supabase()
        .table("agent_runs")
        .select(RUN_FIELDS)
        .eq("owner_id", owner_id)
        .eq("person_id", person_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return jsonify(res.data or [])


@bp.get("/api/runs/<run_id>")
def get_run(run_id):
    owner_id, err = _require_owner_id(request.args.get("owner_id"))
    if err:
        return err
    res = (
        supabase()
        .table("agent_runs")
        .select(RUN_FIELDS)
        .eq("owner_id", owner_id)
        .eq("id", run_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        return jsonify({"error": "not found"}), 404
    return jsonify(rows[0])
