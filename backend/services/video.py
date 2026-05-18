import logging
import uuid

import fal_client
import requests

from config import SUPABASE_VIDEOS_BUCKET
from services.supabase_client import supabase

log = logging.getLogger("video")

FAL_VIDEO_MODEL = "bytedance/seedance-2.0/image-to-video"


def _generate(prompt: str, image_url: str, duration: int = 5) -> bytes:
    if not image_url:
        raise RuntimeError("image_url required")
    log.info("fal video model=%s duration=%ds prompt_len=%d", FAL_VIDEO_MODEL, duration, len(prompt))
    result = fal_client.subscribe(
        FAL_VIDEO_MODEL,
        arguments={
            "prompt": prompt,
            "image_url": image_url,
            "duration": str(duration),
            "resolution": "720p",
            "aspect_ratio": "1:1",
        },
    )
    video = result.get("video") or {}
    video_url = video.get("url") or result.get("video_url")
    if not video_url:
        raise RuntimeError(f"fal returned no video url: {result}")
    log.info("fetching mp4 from %s", video_url)
    return requests.get(video_url, timeout=120).content


def _upload(mp4_bytes: bytes, owner_id: str, run_id: str, kind: str) -> str:
    path = f"{owner_id}/{run_id}/{kind}-{uuid.uuid4()}.mp4"
    sb = supabase()
    sb.storage.from_(SUPABASE_VIDEOS_BUCKET).upload(
        path=path,
        file=mp4_bytes,
        file_options={"content-type": "video/mp4", "upsert": "false"},
    )
    url = sb.storage.from_(SUPABASE_VIDEOS_BUCKET).get_public_url(path)
    log.info("uploaded %s video to %s", kind, url)
    return url


def _smoothie_scene(full_name: str, line: str) -> str:
    return (
        "Scene: a sunny kitchen counter packed with many colorful smoothies in clear "
        "glass cups — strawberry pink, mango orange, green spinach, blueberry purple — "
        "arranged in the foreground in sharp focus, garnished with fruit and straws. "
        f"{full_name} stands in the soft-focus background behind the smoothies, not "
        "the main subject, casually looking toward the camera and speaking warmly with "
        "clear lip sync. Cinematic shallow depth of field, natural daylight, vlog feel. "
        f"They say: \"{line}\""
    )


def generate_intro(person: dict, run_id: str, sms_body: str) -> str:
    full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    prompt = _smoothie_scene(full_name, "Getting you that smoothie now!!")
    mp4 = _generate(prompt, person.get("face_url") or "", duration=5)
    return _upload(mp4, person["owner_id"], run_id, "intro")


def generate_outro(person: dict, run_id: str, result_text: str) -> str:
    full_name = f"{person.get('first_name', '')} {person.get('last_name', '')}".strip()
    prompt = _smoothie_scene(full_name, "Your smoothie should be coming soon")
    mp4 = _generate(prompt, person.get("face_url") or "", duration=5)
    return _upload(mp4, person["owner_id"], run_id, "outro")
