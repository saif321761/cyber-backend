# app/services/n8n_client.py
import httpx
from app.core.config import settings

async def post_to_n8n(payload: dict | list, timeout: float = 10.0) -> dict:
    if not settings.N8N_WEBHOOK_URL:
        return {"ok": False, "reason": "N8N_WEBHOOK_URL not set"}

    def wrap(item):
        if isinstance(item, dict):
            return {"json": item}
        else:
            return {"json": {"value": item}}

    if isinstance(payload, list):
        n8n_payload = [wrap(item) for item in payload]
    else:
        n8n_payload = [wrap(payload)]

    print("DEBUG n8n_payload:", n8n_payload)

    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(settings.N8N_WEBHOOK_URL, json=n8n_payload)
        try:
            return {
                "ok": r.is_success,
                "status_code": r.status_code,
                "response": (
                    r.json()
                    if r.headers.get("content-type", "").startswith("application/json")
                    else r.text
                ),
            }
        except Exception:
            return {
                "ok": r.is_success,
                "status_code": r.status_code,
                "text": r.text,
            }