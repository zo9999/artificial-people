import logging
import threading
import time

from config import DEFAULT_SPEND_CAP_CENTS
from services.supabase_client import supabase
from services import agentphone, browser_use, sponge, persona, voice_agent, video

log = logging.getLogger("runner")

TERMINAL = {"finished", "completed", "succeeded", "success", "failed", "error", "stopped", "cancelled"}


def _guess_merchant(sms_body: str) -> str:
    text = sms_body.lower()
    for m in ("doordash", "uber eats", "instacart", "amazon", "walmart", "target"):
        if m in text:
            return m.title()
    return "Generic"


def _update_run(run_id: str, **fields) -> None:
    try:
        supabase().table("agent_runs").update(fields).eq("id", run_id).execute()
    except Exception:
        log.exception("failed to update run %s", run_id)


def _watch(run_id: str, person: dict, session_id: str, task_id: str | None) -> None:
    log.info("watch start run=%s session=%s", run_id, session_id)
    deadline = time.time() + 15 * 60
    final_status = None
    final_result = ""

    while time.time() < deadline:
        time.sleep(5)
        try:
            sess = browser_use.get_session(session_id)
        except Exception:
            log.exception("poll get_session failed")
            continue
        live_url = sess.get("live_url")
        status = sess.get("status") or ""

        update = {}
        if live_url:
            update["bu_live_url"] = live_url
        if update:
            _update_run(run_id, **update)

        if task_id:
            try:
                t = browser_use.get_task(task_id)
                if t.get("status") in TERMINAL:
                    final_status = t["status"]
                    final_result = t.get("result") or final_result
                    break
            except Exception:
                log.exception("poll get_task failed")

        if status in TERMINAL:
            final_status = status
            break

    succeeded = final_status in {"finished", "completed", "succeeded", "success"}
    final_text = final_result or final_status or "timed out"
    _update_run(
        run_id,
        status="succeeded" if succeeded else "failed",
        result=final_text,
    )

    # Outro video runs in its own thread so it doesn't delay the SMS reply
    threading.Thread(
        target=_generate_outro_async, args=(person, run_id, final_text), daemon=True
    ).start()

    if person.get("phone") and final_result:
        try:
            agentphone.send_message(
                from_number=person["phone"],
                to_number=person.get("_reply_to") or person["phone"],
                body=final_result[:1500],
            )
        except Exception:
            log.exception("failed to send confirmation SMS")

    try:
        voice_agent.refresh_by_id(person["owner_id"], person["id"])
    except Exception:
        log.exception("failed to refresh voice agent after run")

    try:
        browser_use.stop_session(session_id)
    except Exception:
        log.exception("stop_session failed")


def _generate_intro_async(person: dict, run_id: str, sms_body: str) -> None:
    try:
        url = video.generate_intro(person, run_id, sms_body)
        _update_run(run_id, intro_video_url=url)
    except Exception:
        log.exception("intro video generation failed")


def _generate_outro_async(person: dict, run_id: str, result_text: str) -> None:
    try:
        url = video.generate_outro(person, run_id, result_text)
        _update_run(run_id, outro_video_url=url)
    except Exception:
        log.exception("outro video generation failed")


def start_run(person: dict, sms_body: str, reply_to: str | None) -> dict:
    sb = supabase()
    insert = (
        sb.table("agent_runs")
        .insert(
            {
                "owner_id": person["owner_id"],
                "person_id": person["id"],
                "trigger_text": sms_body,
                "status": "running",
            }
        )
        .execute()
    )
    run = (insert.data or [None])[0]
    if not run:
        raise RuntimeError("failed to insert agent_runs row")
    run_id = run["id"]

    merchant = _guess_merchant(sms_body)
    card = {"number": None, "exp": None, "cvc": None}
    try:
        if person.get("sponge_api_key"):
            card = sponge.issue_virtual_card(
                person["sponge_api_key"], merchant, DEFAULT_SPEND_CAP_CENTS
            )
    except Exception:
        log.exception("sponge issue_virtual_card failed (continuing without card)")

    prompt = persona.build_prompt(person, sms_body, card, DEFAULT_SPEND_CAP_CENTS // 100)

    try:
        task = browser_use.create_task(prompt)
    except Exception as e:
        log.exception("browser_use.create_task failed")
        _update_run(run_id, status="failed", result=f"browser-use create_task failed: {e}")
        return {"id": run_id, "status": "failed"}

    session_id = task.get("session_id")
    live_url = None
    if session_id:
        try:
            live_url = browser_use.get_session(session_id).get("live_url")
        except Exception:
            log.exception("browser_use.get_session failed")

    _update_run(run_id, bu_session_id=session_id, bu_live_url=live_url)

    person_ctx = {**person, "_reply_to": reply_to}

    # Generate the intro video in parallel — don't block the browser-use kickoff
    threading.Thread(
        target=_generate_intro_async, args=(person, run_id, sms_body), daemon=True
    ).start()

    if session_id:
        threading.Thread(
            target=_watch,
            args=(run_id, person_ctx, session_id, task.get("task_id")),
            daemon=True,
        ).start()

    return {"id": run_id, "status": "running", "bu_live_url": live_url}
