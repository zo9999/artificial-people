import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_FACES_BUCKET = os.environ.get("SUPABASE_FACES_BUCKET", "faces")

AGENTMAIL_API_KEY = os.environ["AGENTMAIL_API_KEY"]
AGENTMAIL_DOMAIN = os.environ.get("AGENTMAIL_DOMAIN", "agentmail.to")

AGENTPHONE_API_KEY = os.environ["AGENTPHONE_API_KEY"]
AGENTPHONE_BASE_URL = os.environ.get("AGENTPHONE_BASE_URL", "https://api.agentphone.to").rstrip("/")

SPONGE_MASTER_KEY = os.environ["SPONGE_MASTER_KEY"]
SPONGE_BASE_URL = os.environ.get("SPONGE_BASE_URL", "https://api.paysponge.com").rstrip("/")

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "imagen-4.0-generate-001")

PORT = int(os.environ.get("PORT", 5000))
