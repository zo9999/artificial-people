import logging
import uuid

import fal_client
import requests

from config import FAL_IMAGE_MODEL, SUPABASE_FACES_BUCKET
from services.supabase_client import supabase

log = logging.getLogger("face")

_PORTRAIT_TEMPLATE = (
    "Photorealistic studio headshot portrait, neutral light gray background, "
    "soft natural lighting, subject looking directly at camera, sharp focus, "
    "shallow depth of field, professional photography. Subject: {prompt}"
)


def generate_and_upload_face(prompt: str, owner_id: str) -> tuple[str, str]:
    full_prompt = _PORTRAIT_TEMPLATE.format(prompt=prompt.strip())
    log.info("generating face model=%s", FAL_IMAGE_MODEL)

    result = fal_client.subscribe(
        FAL_IMAGE_MODEL,
        arguments={
            "prompt": full_prompt,
            "image_size": "square_hd",
            "num_images": 1,
        },
    )
    images = result.get("images") or []
    if not images:
        raise RuntimeError("fal returned no images")
    src_url = images[0].get("url")
    if not src_url:
        raise RuntimeError("fal image missing url")

    img_bytes = requests.get(src_url, timeout=30).content

    path = f"{owner_id}/{uuid.uuid4()}.png"
    sb = supabase()
    sb.storage.from_(SUPABASE_FACES_BUCKET).upload(
        path=path,
        file=img_bytes,
        file_options={"content-type": "image/png", "upsert": "false"},
    )
    public_url = sb.storage.from_(SUPABASE_FACES_BUCKET).get_public_url(path)
    log.info("uploaded face to %s", public_url)
    return public_url, full_prompt
