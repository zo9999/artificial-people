import logging

from openai import OpenAI

from config import OPENAI_API_KEY

log = logging.getLogger("intent")
_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

_SYSTEM = (
    "You decide whether an inbound SMS to an AI assistant is an actionable task it "
    "should attempt to complete on the open web (ordering food, buying things, signing "
    "up for services, booking, etc.), or whether it is something it should ignore "
    "(2FA / verification codes, marketing, OTP receipts, delivery confirmations, "
    "chit-chat, replies it sent itself, automated notifications).\n\n"
    "Reply with exactly one token: ACT or IGNORE. No other output."
)


def is_actionable(sms_body: str) -> bool:
    """Return True if the SMS looks like a fresh user instruction to do something.

    Fail-open: if OpenAI isn't configured or the call fails, default to True so
    we don't drop real requests on the floor.
    """
    text = (sms_body or "").strip()
    if not text:
        return False
    if not _client:
        log.warning("OPENAI_API_KEY not set; treating SMS as actionable")
        return True
    try:
        resp = _client.responses.create(
            model="gpt-5-mini",
            input=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": text},
            ],
        )
        out = (resp.output_text or "").strip().upper()
        log.info("intent for %r → %s", text[:80], out)
        return out.startswith("ACT")
    except Exception:
        log.exception("intent classify failed; defaulting to actionable")
        return True
