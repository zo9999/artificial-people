import os

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_FACES_BUCKET = os.environ.get("SUPABASE_FACES_BUCKET", "faces")

AGENTMAIL_API_KEY = os.environ.get("AGENTMAIL_API_KEY", "")
AGENTMAIL_DOMAIN = os.environ.get("AGENTMAIL_DOMAIN", "agentmail.to")

AGENTPHONE_API_KEY = os.environ.get("AGENTPHONE_API_KEY", "")
AGENTPHONE_BASE_URL = os.environ.get("AGENTPHONE_BASE_URL", "https://api.agentphone.to").rstrip("/")

SPONGE_MASTER_KEY = os.environ.get("SPONGE_MASTER_KEY", "")
SPONGE_BASE_URL = os.environ.get("SPONGE_BASE_URL", "https://api.paysponge.com").rstrip("/")

FAL_KEY = os.environ.get("FAL_KEY", "")
FAL_IMAGE_MODEL = os.environ.get("FAL_IMAGE_MODEL", "fal-ai/flux/schnell")

SUPERMEMORY_API_KEY = os.environ["SUPERMEMORY_API_KEY"]

BROWSER_USE_API_KEY = os.environ.get("BROWSER_USE_API_KEY", "")
BROWSER_USE_BASE_URL = os.environ.get("BROWSER_USE_BASE_URL", "https://api.browser-use.com/api/v2").rstrip("/")
AGENTPHONE_WEBHOOK_SECRET = os.environ.get("AGENTPHONE_WEBHOOK_SECRET", "")
PUBLIC_WEBHOOK_BASE = os.environ.get("PUBLIC_WEBHOOK_BASE", "").rstrip("/")
DEFAULT_SPEND_CAP_CENTS = int(os.environ.get("DEFAULT_SPEND_CAP_CENTS", "5000"))

PORT = int(os.environ.get("PORT", 5000))
