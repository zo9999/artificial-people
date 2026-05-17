import base64
import uuid

from google import genai

from config import GEMINI_API_KEY, GEMINI_IMAGE_MODEL, SUPABASE_FACES_BUCKET
from services.supabase_client import supabase

_client = genai.Client(api_key=GEMINI_API_KEY)

_PORTRAIT_TEMPLATE = (
    "Photorealistic studio headshot portrait, neutral light gray background, "
    "soft natural lighting, subject looking directly at camera, sharp focus, "
    "shallow depth of field, professional photography. Subject: {prompt}"
)


def _extract_image_bytes(response) -> bytes:
    images = getattr(response, "generated_images", None)
    if not images:
        raise RuntimeError("Gemini returned no images")
    image_obj = images[0].image
    data = getattr(image_obj, "image_bytes", None)
    if data:
        return data if isinstance(data, bytes) else base64.b64decode(data)
    raise RuntimeError("Gemini image missing bytes")


def generate_and_upload_face(prompt: str, owner_id: str) -> tuple[str, str]:
    full_prompt = _PORTRAIT_TEMPLATE.format(prompt=prompt.strip())
    response = _client.models.generate_images(
        model=GEMINI_IMAGE_MODEL,
        prompt=full_prompt,
        config={"number_of_images": 1, "aspect_ratio": "1:1"},
    )
    img_bytes = _extract_image_bytes(response)

    path = f"{owner_id}/{uuid.uuid4()}.png"
    sb = supabase()
    sb.storage.from_(SUPABASE_FACES_BUCKET).upload(
        path=path,
        file=img_bytes,
        file_options={"content-type": "image/png", "upsert": "false"},
    )
    public_url = sb.storage.from_(SUPABASE_FACES_BUCKET).get_public_url(path)
    return public_url, full_prompt
