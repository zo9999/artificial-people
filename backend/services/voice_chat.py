import logging

from openai import OpenAI

from config import OPENAI_API_KEY

log = logging.getLogger("voice_chat")
_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MODEL = "gpt-4.1-nano"


def _persona(person: dict) -> str:
    full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    return (
        f"You are {full_name}. Speak as yourself in casual, natural English. "
        "Hard rules: reply in ONE short sentence (max ~15 words). "
        "Never say you are an AI, assistant, bot, or artificial. "
        "This is a live phone call, so be conversational and avoid emojis."
    )


def ack_action(action_description: str = "") -> str:
    """Canned reply when the caller asks for an actionable task.

    Skips an LLM call to keep latency tight.
    """
    return "On it — hanging up and I'll text you when it's done."


def reply(person: dict, recent_messages: list[dict], utterance: str) -> str:
    """Generate a single short voice reply using gpt-4.1-nano."""
    if not _client:
        log.warning("OPENAI_API_KEY not set")
        return "Hey, what's up?"

    msgs = [{"role": "system", "content": _persona(person)}]
    for m in (recent_messages or [])[-8:]:
        role = (m.get("role") or "").lower()
        if role in ("agent", "assistant"):
            mapped = "assistant"
        elif role in ("user", "caller", "human"):
            mapped = "user"
        else:
            continue
        content = m.get("content") or m.get("text") or m.get("transcript") or ""
        if content:
            msgs.append({"role": mapped, "content": content})
    msgs.append({"role": "user", "content": utterance})

    try:
        resp = _client.responses.create(model=MODEL, input=msgs)
        text = (resp.output_text or "").strip()
        return text or "Yeah?"
    except Exception:
        log.exception("voice reply failed")
        return "Hmm, what was that?"
