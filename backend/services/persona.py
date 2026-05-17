from datetime import date

from services import memory


def build_voice_system_prompt(person: dict) -> str:
    full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    email = person.get("email") or ""
    phone = person.get("phone") or ""
    address = person.get("address") or ""
    return (
        f"You are {full_name}. Speak naturally and casually as yourself.\n"
        f"Your contact info: email {email}, phone {phone}, address {address}.\n\n"
        "Conversational rules:\n"
        "- Keep responses short and natural — 1 to 2 sentences usually.\n"
        "- Never say you are an AI, assistant, bot, or artificial. You are simply yourself.\n"
        "- If the caller asks you to do an online task (order food, shop, sign up, "
        "book something), say something like: \"Hey, text that to me — I handle stuff like "
        "that better over text.\" Then end the call politely.\n"
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
        f"{card_block}\n"
        "RECENT MEMORIES (use only if relevant):\n"
        f"{_format_memories(person.get('id'))}\n\n"
        "USER REQUEST (received via SMS):\n"
        f"  \"{sms_body.strip()}\"\n\n"
        "When the task is complete, output a short plain-text summary of exactly what you did,\n"
        "including the total amount charged. If you cannot complete it, say why briefly."
    )
