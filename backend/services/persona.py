from datetime import date

from config import PUBLIC_WEBHOOK_BASE
from services import memory


def _format_runs_for_voice(runs: list[dict]) -> str:
    lines = []
    for r in runs[:5]:
        trig = (r.get("trigger_text") or "").strip()
        status = r.get("status") or ""
        result = (r.get("result") or "").strip().splitlines()[:1]
        result_one_line = result[0] if result else ""
        when = (r.get("created_at") or "")[:10]
        bits = [f"{when} — {trig}", f"[{status}]"]
        if result_one_line:
            bits.append(result_one_line)
        lines.append("- " + " ".join(bits))
    return "\n".join(lines) if lines else "(no recent tasks)"


def _format_memories_for_voice(memories: list[dict]) -> str:
    lines = []
    for m in memories[:10]:
        c = (m.get("content") or "").strip()
        if c:
            lines.append(f"- {c}")
    return "\n".join(lines) if lines else "(no memories)"


def build_voice_system_prompt(
    person: dict,
    runs: list[dict] | None = None,
    memories: list[dict] | None = None,
) -> str:
    full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    email = person.get("email") or ""
    phone = person.get("phone") or ""
    address = person.get("address") or ""
    runs = runs or []
    memories = memories or []
    return (
        f"You are {full_name}. Speak naturally and casually as yourself.\n"
        f"Your contact info: email {email}, phone {phone}, address {address}.\n\n"
        "WHAT YOU REMEMBER:\n"
        f"{_format_memories_for_voice(memories)}\n\n"
        "RECENT THINGS YOU'VE DONE (from your assistant runs):\n"
        f"{_format_runs_for_voice(runs)}\n\n"
        "Conversational rules:\n"
        "- Keep responses short and natural — 1 to 2 sentences usually.\n"
        "- Never say you are an AI, assistant, bot, or artificial. You are simply yourself.\n"
        "- If the caller asks what you've been up to, summarize the recent things above casually.\n"
        "- If the caller asks you to do an online task (order food, shop, sign up, "
        "book something), say: \"Hey, text that to me — I handle stuff like that better over text.\" "
        "Then end the call politely.\n"
        "- For small talk or simple questions, answer briefly and stay in character."
    )


def _format_memories(person_id: str) -> str:
    try:
        items = memory.search_memories(person_id, None)[:10]
    except Exception:
        return "(none)"
    if not items:
        return "(none)"
    return "\n".join(f"- {m.get('content', '').strip()}" for m in items if m.get("content"))


def build_prompt(person: dict, sms_body: str, card: dict, spend_cap_dollars: int) -> str:
    full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    email = person.get("email") or "(none)"
    phone = person.get("phone") or "(none)"
    address = person.get("address") or "(none)"
    today = date.today().isoformat()

    card_block = (
        "PAYMENT — use this one-time virtual card for THIS task only:\n"
        f"  cardholder name: {full_name}\n"
        f"  number: {card.get('number', '(missing)')}\n"
        f"  expiration: {card.get('exp', '(missing)')}\n"
        f"  cvc: {card.get('cvc', '(missing)')}\n"
        f"  spending cap: ${spend_cap_dollars}. DO NOT exceed it.\n"
    )

    creds = (person.get("credentials_text") or "").strip()
    creds_block = (
        "\nSTORED CREDENTIALS / NOTES (use as needed, treat as sensitive):\n"
        f"{creds}\n"
    ) if creds else ""

    inbox_url = (
        f"{PUBLIC_WEBHOOK_BASE}/api/inbox/{person.get('id')}/latest"
        if PUBLIC_WEBHOOK_BASE and person.get("id") else ""
    )
    inbox_block = (
        "\nSMS INBOX (for 2FA / verification codes texted to your phone):\n"
        f"  Open {inbox_url} in the browser to view your latest inbound SMS messages\n"
        "  as plain text. Re-load the page to see new messages. Any short 4–8 digit\n"
        "  code in a recent message is almost certainly the 2FA code you need.\n"
    ) if inbox_url else ""

    return (
        f"You are {full_name}, an artificial person. Today is {today}.\n\n"
        "IDENTITY:\n"
        f"  name: {full_name}\n"
        f"  email: {email}\n"
        f"  phone: {phone}\n"
        f"  shipping address: {address}\n\n"
        "EMAIL VERIFICATION:\n"
        "  If a site sends you an email verification code or magic link, sign in to your\n"
        f"  AgentMail inbox at https://app.agentmail.to/ as {email} and retrieve the latest message.\n\n"
        f"{card_block}"
        f"{creds_block}"
        f"{inbox_block}\n"
        "RECENT MEMORIES (use only if relevant):\n"
        f"{_format_memories(person.get('id'))}\n\n"
        "USER REQUEST (received via SMS):\n"
        f"  \"{sms_body.strip()}\"\n\n"
        "When the task is complete, output a short plain-text summary of exactly what you did,\n"
        "including the total amount charged. If you cannot complete it, say why briefly."
    )
