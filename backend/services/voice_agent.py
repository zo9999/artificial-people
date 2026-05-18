import logging

from services.supabase_client import supabase
from services import agentphone, memory, persona

log = logging.getLogger("voice_agent")


def _load_runs(owner_id: str, person_id: str) -> list[dict]:
    res = (
        supabase()
        .table("agent_runs")
        .select("trigger_text, status, result, created_at")
        .eq("owner_id", owner_id)
        .eq("person_id", person_id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    return res.data or []


def _load_memories(person_id: str) -> list[dict]:
    try:
        return memory.search_memories(person_id, None)[:10]
    except Exception:
        log.exception("memory load failed (continuing)")
        return []


def refresh(person: dict) -> None:
    """Push the latest system prompt (with recent runs + memories) to the AP's voice agent."""
    agent_id = person.get("agentphone_agent_id")
    if not agent_id:
        log.info("refresh skipped (no agentphone_agent_id)")
        return
    runs = _load_runs(person["owner_id"], person["id"])
    memories = _load_memories(person["id"])
    prompt = persona.build_voice_system_prompt(person, runs=runs, memories=memories)
    try:
        agentphone.update_agent(
            agent_id,
            voiceMode="hosted",
            systemPrompt=prompt,
            messagingTools=True,
        )
        log.info("refreshed voice agent %s", agent_id)
    except Exception:
        log.exception("refresh voice agent failed")


def refresh_by_id(owner_id: str, person_id: str) -> None:
    res = (
        supabase()
        .table("people")
        .select("*")
        .eq("owner_id", owner_id)
        .eq("id", person_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if rows:
        refresh(rows[0])
