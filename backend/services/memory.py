import logging

from supermemory import Supermemory

from config import SUPERMEMORY_API_KEY

log = logging.getLogger("memory")
_client = Supermemory(api_key=SUPERMEMORY_API_KEY)


def _tag(person_id: str) -> str:
    return f"ap:{person_id}"


def add_memory(person_id: str, owner_id: str, content: str) -> dict:
    log.info("add_memory person=%s len=%d", person_id, len(content))
    doc = _client.add(
        content=content,
        container_tags=[_tag(person_id)],
        metadata={"owner_id": owner_id, "person_id": person_id},
    )
    return {
        "id": getattr(doc, "id", None) or getattr(doc, "document_id", None),
        "content": content,
    }


def _result_to_dict(item) -> dict:
    if isinstance(item, dict):
        d = item
    else:
        d = {
            k: getattr(item, k, None)
            for k in (
                "id",
                "content",
                "summary",
                "score",
                "metadata",
                "created_at",
                "createdAt",
                "updated_at",
            )
        }
    return {
        "id": d.get("id") or d.get("document_id"),
        "content": d.get("content") or d.get("summary") or "",
        "score": d.get("score"),
        "created_at": d.get("created_at") or d.get("createdAt"),
    }


def _iter_response_items(res) -> list:
    for attr in ("results", "documents", "items", "data"):
        v = getattr(res, attr, None)
        if v is not None:
            return list(v)
    if isinstance(res, list):
        return res
    return []


def search_memories(person_id: str, query: str | None) -> list[dict]:
    log.info("search_memories person=%s q=%r", person_id, query)
    tag = _tag(person_id)
    if query:
        res = _client.search.documents(q=query, container_tags=[tag])
    else:
        res = _client.documents.list(container_tags=[tag], limit=50)
    return [_result_to_dict(i) for i in _iter_response_items(res)]
